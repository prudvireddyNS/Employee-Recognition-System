import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { Card, CardContent } from './components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import debounce from 'lodash/debounce';

const SearchInterface = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [topK, setTopK] = useState('3');

  // Debounce the search to avoid too many API calls
  const debouncedSearch = debounce(async (searchQuery) => {
    if (searchQuery.trim() === '') {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: searchQuery,
          top_k: parseInt(topK)
        }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  }, 300);

  useEffect(() => {
    return () => {
      debouncedSearch.cancel();
    };
  }, []);

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSearch(value);
  };

  const handleTopKChange = (value) => {
    setTopK(value);
    if (query.trim()) {
      debouncedSearch(query);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-4">Support Ticket Search</h1>
        <div className="flex gap-4 items-start">
          <div className="relative flex-1">
            <Input
              type="text"
              placeholder="Start typing to search similar support tickets..."
              value={query}
              onChange={handleInputChange}
              className="w-full pl-10"
            />
            <Search className="w-5 h-5 absolute left-3 top-2 text-gray-400" />
          </div>
          <Select value={topK} onValueChange={handleTopKChange}>
            <SelectTrigger className="w-24">
              <SelectValue placeholder="Results" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Top 1</SelectItem>
              <SelectItem value="3">Top 3</SelectItem>
              <SelectItem value="5">Top 5</SelectItem>
              <SelectItem value="10">Top 10</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading && (
        <div className="flex justify-center my-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      )}

      <div className="space-y-4">
        {results.map((result, index) => (
          <Card key={index}>
            <CardContent className="p-4">
              <div className="mb-2">
                <div className="font-semibold text-lg mb-1">Similar Question:</div>
                <p className="text-gray-700">{result.description}</p>
              </div>
              <div>
                <div className="font-semibold text-lg mb-1">Solution:</div>
                <p className="text-gray-700">{result.solution}</p>
              </div>
              <div className="mt-2 text-sm text-gray-500">
                Similarity Score: {(result.score * 100).toFixed(1)}%
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {query && !loading && results.length === 0 && (
        <div className="text-center text-gray-500 mt-4">
          No matching tickets found
        </div>
      )}
    </div>
  );
};

export default SearchInterface;
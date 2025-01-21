import click
from backend.database import SessionLocal, AdminUser
from backend.auth import get_password_hash

@click.command()
@click.option('--username', prompt='Enter admin username')
@click.option('--password', prompt='Enter admin password', hide_input=True)
def create_admin(username, password):
    """Create a new admin user"""
    db = SessionLocal()
    try:
        # Check if admin exists
        existing_admin = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing_admin:
            click.echo(f"Admin user '{username}' already exists!")
            return

        # Create new admin
        admin = AdminUser(
            username=username,
            password_hash=get_password_hash(password),
            is_active=True
        )
        db.add(admin)
        db.commit()
        click.echo(f"Admin user '{username}' created successfully!")
    except Exception as e:
        db.rollback()
        click.echo(f"Error creating admin: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    create_admin()

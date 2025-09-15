import click
from app import create_app, db
from app.models.user import User
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

@app.cli.command("create-admin")
@click.argument("name")
@click.argument("phone")
@click.argument("address")
def create_admin(name, phone, address):
    u = User(name=name, phone=phone, role="admin", address=address, is_available=False, has_vehicle=False, capacity=0)
    db.session.add(u)
    db.session.commit()
    click.echo(f"Admin créé: id={u.id} name={u.name}")

if __name__ == "__main__":
    app.run()

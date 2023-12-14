from flask import Flask

from models.electro_scooter import ElectroScooter
from models.database import db
from config import node


def create_app():
    db_name = 'scooter'
    if node.role != 'leader':
        db_name += str(node.to_string()['port'])

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_name}.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    return app


if __name__ == '__main__':
    app = create_app()
    import routes
    with app.app_context():
        db.create_all()
        sample_scooter_1 = ElectroScooter(name="Scooter 1", battery_level=90.5)
        sample_scooter_2 = ElectroScooter(name="Scooter 2", battery_level=80.0)
        db.session.add(sample_scooter_1)
        db.session.add(sample_scooter_2)

        db.session.commit()

    app.run(
        host=node.info['host'],
        port=node.info['port']
    )

from src import database as db
import sqlalchemy as sa
import factory

class SQLAlchemyCoreFactory(factory.Factory):
    class Meta:
        abstract = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        with db.engine.begin() as connection:
            result = connection.execute(model_class.insert().values(**kwargs))
        return result.inserted_primary_key
    
    @classmethod
    def _build(model_class, *args, **kwargs):
        return kwargs


class FightersFactory(SQLAlchemyCoreFactory):
    class Meta:
        model = db.fighters
    
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    height = factory.Faker(
        'pyint',
        min_value=60,
        max_value=90,
    )
    reach = factory.Faker(
        'pyint',
        min_value=60,
        max_value=90,
    )
    # Can technically be more correct if we queried the database, but it's such a waste
    stance_id = factory.Faker(
        'pyint',
        min_value=1,
        max_value=3,
    )
    


class FighterStatsFactory(SQLAlchemyCoreFactory):
    class Meta:
        model = db.fights
    
    kd = factory.Faker(
        'pyint',
        min_value=0,
        max_value=100,
    )
    strikes = factory.Faker(
        'pyint',
        min_value=0,
        max_value=100,
    )
    td = factory.Faker(
        'pyint',
        min_value=0,
        max_value=100,
    )
    sub = factory.Faker(
        'pyint',
        min_value=0,
        max_value=100,
    )
    weight = factory.Faker(
        'pyint',
        min_value=120,
        max_value=400,
    )
    fighter_id = factory.Iterator(db.fighters)

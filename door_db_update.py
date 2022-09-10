# %%
from sqlalchemy import create_engine, Table, MetaData, insert, delete

# %%
engine = create_engine('sqlite:///balllab.db', echo=True)

doorstatus = Table('door_status', MetaData(), autoload=True, autoload_with=engine)


# %%
with engine.connect() as conn:
    result = conn.execute(
        insert(doorstatus), 
        [
            {"area":"center_1", "status":'0'},
            {"area":"center_2_3f", "status":'0'},
            {"area":"center_2_4f", "status":'0'},
        ]
        
    )

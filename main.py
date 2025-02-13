from graphql_app.schema import schema
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


# import graphql_app.config
# import mysql.connector
#
# conf = graphql_app.config.Config("config/config.ini")
# mydb = mysql.connector.connect(**conf.load_db_config())

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
]

# GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":

    #run sever
    uvicorn.run(app, host="127.0.0.1", port=8000)


    # cursor = mydb.cursor()
    # cursor.execute("SHOW DATABASES")
    # for db in cursor.fetchall():
    #     print(db)
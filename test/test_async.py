import asyncio
import pytest
from graphql_app.schema import schema


@pytest.mark.asyncio
async def test_query_async():
    query = """
        query TestQuery($id: Int!) {
            getUser(id: $id) {
                id
                email
            }
        }
    """
    res = await schema.execute(query, variable_values={"id": 22})

    assert res.errors is None, f"GraphQL Errors: {res.errors}"
    assert res.data["getUser"] == {
        "id": 22,
        "email": "bell77m@gmail.com",
    }

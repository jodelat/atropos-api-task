from datetime import timedelta
import bcrypt
from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from jwt import PyJWTError
from ariadne import QueryType, MutationType, make_executable_schema, graphql
from ariadne.asgi import GraphQL
from celery_worker import create_task
from db_conf import db_session
from jwt_token import create_access_token, decode_access_token
from schemas import PostModel, PostSchema, UserSchema
import models

# Initialize database session
db = db_session.session_factory()

# Initialize FastAPI app
app = FastAPI()

# Celery Task API
@app.post("/ex1")
def run_task(data=Body(...)):
    amount = int(data["amount"])
    x = data["x"]
    y = data["y"]
    task = create_task.delay(amount, x, y)
    return JSONResponse({"Result": task.get()})

# Define QueryType resolvers for GraphQL
query = QueryType()

@query.field("allPosts")
def resolve_all_posts(_, info):
    return db.query(models.Post).all()

@query.field("postById")
def resolve_post_by_id(_, info, post_id):
    return db.query(models.Post).filter(models.Post.id == post_id).first()

# Define MutationType resolvers for GraphQL
mutation = MutationType()

@mutation.field("authenticateUser")
def resolve_authenticate_user(_, info, username, password):
    user = UserSchema(username=username, password=password)
    db_user_info = db.query(models.User).filter(models.User.username == username).first()

    if bcrypt.checkpw(user.password.encode("utf-8"), db_user_info.password.encode("utf-8")):
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(data={"user": username}, expires_delta=access_token_expires)
        return {"ok": True, "token": access_token}
    return {"ok": False}

@mutation.field("createNewUser")
def resolve_create_new_user(_, info, username, password):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf8")
    user = UserSchema(username=username, password=hashed_password)
    db_user = models.User(username=user.username, password=hashed_password)
    db.add(db_user)

    try:
        db.commit()
        db.refresh(db_user)
        return {"ok": True}
    except:
        db.rollback()
        return {"ok": False}

@mutation.field("createNewPost")
def resolve_create_new_post(_, info, title, content, token):
    try:
        payload = decode_access_token(data=token)
        username = payload.get("user")
        if not username:
            return {"result": "Invalid credentials 1"}
    except PyJWTError:
        return {"result": "Invalid credentials 2"}

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return {"result": "Invalid credentials 3"}

    post = PostSchema(title=title, content=content)
    db_post = models.Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return {"result": "Added new post"}

# Define GraphQL schema
type_defs = """
    type Post {
        id: ID!
        title: String!
        content: String!
    }

    type Query {
        allPosts: [Post!]
        postById(postId: Int!): Post
    }

    type Mutation {
        authenticateUser(username: String!, password: String!): AuthPayload!
        createNewUser(username: String!, password: String!): UserPayload!
        createNewPost(title: String!, content: String!, token: String!): PostPayload!
    }

    type AuthPayload {
        ok: Boolean!
        token: String
    }

    type UserPayload {
        ok: Boolean!
    }

    type PostPayload {
        result: String!
    }
"""

schema = make_executable_schema(type_defs, query, mutation)

# Add Ariadne's GraphQL middleware
app.add_route("/graphql", GraphQL(schema=schema))

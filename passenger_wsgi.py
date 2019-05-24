import sys, os
import time
import logging
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
from sqlalchemy import create_engine, select, MetaData, Table, insert, or_, func
from newsapi.newsapi_client import NewsApiClient
from data.data import News, Tags, User, Post

INTERP = os.path.join(os.environ['HOME'], 'api.mikn.app', 'venv/bin', 'python')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('apilog.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

newsapi = NewsApiClient(api_key='1654f224d44d4dc491f416ef7950a051')

db_connect = create_engine('mysql+pymysql://phelper:Lscooter11@mysql.monkeyandjoe.com:3306/phelper')
application = Flask(__name__)
application.config['CORS_HEADERS'] = 'Content-Type'
api = Api(application)
cors = CORS(application, resources={r"*": {"origins": "*"}})

# DB Setup
meta = MetaData(db_connect, reflect=True)
user_prefs_t = meta.tables['userprefs']

# Classes
tagsclass = Tags()
newsclass = News()
userclass = User()
postclass = Post()


@application.route('/')
# @application.route('/implicit/callback')
@cross_origin(origin="*", headers=['Content- Type', 'Authorization'])
def index():
    return 'hello'


class Tags(Resource):
    def get(self):
        top = request.args.get('top')
        result = tagsclass.gettags(top=top)
        return result

    def put(self):
        tag = request.json['tag']
        query = tagsclass.addtags(tag=tag)
        return query


class Auth(Resource):
    def post(self):
        new = request.args.get('new')
        password = request.json['password']
        username = request.json['username']
        firstname = request.json['firstName'] if new else None
        lastname = request.json['lastName'] if new else None
        email = request.json['email'] if new else None

        query = userclass.authorizeuser(new=new, password=password, username=username, firstname=firstname,lastname=lastname,email=email)
        return query


# edit to look up id by name and for creating a new tag also add to post
#combine Tags class
# Posts
class PostTags(Resource):
    def put(self):
        add = request.args.get('add')
        delete = request.args.get('delete')
        tags = request.json['tags']
        taskid = request.json['taskid']
        query = Post.manageposttag(add=add,delete=delete,postid=taskid,tagid=tags)
        return query


class NewTasksInternal(Resource):
    def post(self):
        task = request.json['task']
        familyid = request.json['familyid']
        approved = request.json['approved']
        title = request.json['title']
        summary = request.json['summary']
        query = postclass.newpost(
            task=task,
            familyid=familyid,
            approved=approved,
            title=title,
            summary=summary
        )
        return query

# Users

class UsersAll(Resource):
    def get(self):
        conn = db_connect.connect()
        query = conn.execute("select *  from person a")
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)


class UserEmail(Resource):
    def get(self, email):
        conn = db_connect.connect()
        query = conn.execute("select a.familyid from person a  where a.email  ='{0}'".format(email))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return result[0]


# class UserTasks(Resource):
#     def get(self, familyid):
#         conn = db_connect.connect()
#         query = conn.execute(
#             "select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null group by a.task,a.id,a.familyid order by lastupdate desc".format(
#                 familyid))
#         result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
#         return jsonify(result)


# class UserToDo(Resource):
#     def get(self, familyid):
#         conn = db_connect.connect()
#         param = 'todo'
#         query = conn.execute(
#             "select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null and c.tag like '{1}' group by a.task,a.id,a.familyid order by lastupdate desc".format(
#                 familyid, (param)))
#         result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
#         return jsonify(result)


# class UserPostsByTag(Resource):
#     def get(self, tag):
#         conn = db_connect.connect()
#         query = conn.execute(
#             "select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  = 4 and approved is not null and c.tag = '{0}' group by a.task,a.id,a.familyid order by lastupdate desc".format(
#                 tag))
#         result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
#         return jsonify(result)


# class UserToRead(Resource):
#     def get(self, familyid):
#         conn = db_connect.connect()
#         query = conn.execute(
#             "select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null and lower(c.tag) = 'want to read' group by a.task,a.id,a.familyid order by lastupdate desc".format(
#                 familyid))
#         result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
#         return jsonify(result)


# class UserArchived(Resource):
#     def get(self, familyid):
#         conn = db_connect.connect()
#         query = conn.execute(
#             "select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null and lower(c.tag) = 'archive' group by a.task,a.id,a.familyid order by lastupdate desc".format(
#                 familyid))
#         result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
#         return jsonify(result)


class UserRecentlyAdded(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute(
            "select a.addedts, a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  = '{0}' and a.addedts > NOW() - INTERVAL 1 WEEK and approved is not null and (b.taskid not in (select taskid from taskids a join tags b on a.tagid = b.id where lower(b.tag) = 'archive') or b.taskid is null)  group by a.task,a.id,a.familyid order by addedts desc limit 5".format(
                familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)


# class UserTasksMostRead(Resource):
#     def get(self, familyid):
#         conn = db_connect.connect()
#         query = conn.execute(
#             "select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag)  as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null and readcount > 0 and Lower(c.tag) <> 'archive' group by a.task,a.id,a.familyid   order by readcount desc".format(
#                 familyid))
#         result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
#         return jsonify(result)


# class ApprovalQueue(Resource):
#     def get(self, familyid):
#         conn = db_connect.connect()
#         query = conn.execute(
#             "select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is null group by a.task,a.id,a.familyid order by lastupdate desc".format(
#                 familyid))
#         result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
#         return jsonify(result)


class Userlists(Resource):
    def get(self, familyid):
        logging.info('connecting')
        conn = db_connect.connect()
        query = conn.execute(
            "select GROUP_CONCAT(name) as name from userlists  where familyid  ='{0}'".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        logging.info(result)
        return result[0]

    def put(self, familyid):
        logging.info('connecting')
        conn = db_connect.connect()
        name = request.json['name']
        query = conn.execute("insert into userlists(familyid,name) values('{0}','{1}')".format(familyid, name))
        return {'status': 'success'}

    def delete(self, familyid):
        logging.info('connecting')
        conn = db_connect.connect()
        name = request.json['name']
        query = conn.execute("delete from userlists where name = '{1}' and familyid = '{0}'".format(familyid, name))
        return {'status': 'success'}


class Userlistposts(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute(
            "select postid as id,c.title as title, a.name as status  from userlists a join userlistposts b on a.id = b.listid join tasks c on b.postid = c.id  where a.familyid  ='{0}'".format(
                familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

    def put(self, familyid):
        logging.debug(request.json)
        conn = db_connect.connect()
        postid = request.json['id']
        status = request.json['status']
        query = conn.execute(
            "UPDATE userlistposts SET userlistposts.listid = (select id from userlists where userlists.name = '{0}' and familyid ='{2}' ) where userlistposts.postid = '{1}'".format(
                status, postid, familyid))
        return {'status': 'success'}

    def post(self, familyid):
        logging.info(request.json)
        conn = db_connect.connect()
        postid = request.json['postid']
        name = request.json['name']
        listid = request.json['listid']
        query = conn.execute(
            "insert into userlistposts(postid,listid,name) values('{1}',(select id from userlists where name = '{0}' and familyid = '{3}'),(select title from tasks where id = '{2}'))".format(
                listid, postid, name, familyid))
        return {'status': 'success'}

    def delete(self, familyid):
        logging.info(request.json)
        conn = db_connect.connect()
        postid = request.json['postid']
        listid = request.json['listid']
        query = conn.execute(
            "delete from userlistposts where postid = '{0}' and listid = (select id from userlists where name = '{1}' and familyid = '{2}') ".format(
                postid, listid, familyid))
        return {'status': 'success'}


# class ApproveTask(Resource):
#     def put(self, id):
#         conn = db_connect.connect()  # connect to database
#         query = conn.execute("update tasks set approved  = 1  where id = {0}".format(id))
#         return {'status': 'success'}


class PostList(Resource):
    def get(self, id):
        conn = db_connect.connect()
        query = conn.execute(
            "select a.name as listname from userlists a join userlistposts b on a.id = b.listid where b.postid = '{0}'".format(
                id))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)


class TaskDetail(Resource):
    def put(self, id):
        conn = db_connect.connect()  # connect to database
        logging.info(request)
        logging.info(request.json)
        taskraw = request.json['task']
        task = taskraw.replace("'", "")
        titleraw = request.json['title']
        title = titleraw.replace("'", "")
        summaryraw = request.json['summary']
        summary = summaryraw.replace("'", "")
        query = conn.execute(
            "update tasks set task = '{0}', title = '{2}',summary = '{3}'  where id = {1}".format(task, id, title,
                                                                                                  summary))
        query2 = conn.execute("select * from tasks where id = '{0}'".format(id))
        result = [dict(zip(tuple(query2.keys()), i)) for i in query2.cursor]
        return jsonify(result)

    def delete(self, id):
        logging.info('connecting')
        conn = db_connect.connect()
        logging.info('connected')
        logging.debug(request.json)
        print(request.json)
        query = conn.execute("delete from tasks where id = '{0}'".format(id))
        query2 = conn.execute("delete from userlistposts where postid = '{0}'".format(id))
        return {'status': 'success'}

    def get(self, id):
        conn = db_connect.connect()
        query = conn.execute(
            "select a.approved, a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where a.id  ='{0}' group by a.task,a.id,a.familyid".format(
                id))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

    def post(self, id):
        conn = db_connect.connect()
        query = conn.execute("update tasks set readcount = readcount+1 where id = {0}".format(id))
        return {'status': 'read count updated'}


class GetNewsSources(Resource):

    def get(self):
        sourcesorig = newsapi.get_sources()
        sources = sourcesorig['sources']
        return sources

    def put(self):
        dbstart = time.time()
        logger.info(dbstart)
        conn = db_connect.connect()
        dbend = time.time()
        logger.info(dbend)
        source = request.json['sourcedata']['id']
        user = request.json['family']['familyid']
        paramtype = '2'

        userprefs = Table('userprefs', meta)

        ins = userprefs.insert().values(
            variable=paramtype,
            prefvalue=source,
            userid=user
        )

        try:
            conn.execute(ins)

            status = 'New Source Added'
            output = jsonify(status)

        except:

            status = 'Source Not Added'
            output = jsonify(status)

        return output


class GetUsersNews(Resource):

    def get(self, familyid):
        start = time.time()
        logger.info(start)
        conn = db_connect.connect()
        q = select([user_prefs_t.c.prefvalue, user_prefs_t.c.id]).where(user_prefs_t.c.variable == 2).where(
            user_prefs_t.c.userid == familyid)
        query = conn.execute(q)
        topiclist = ','.join([r[0] for r in query.cursor.fetchall()])
        dbend = time.time()
        logger.info(dbend)
        logging.info(q)
        logging.info('test')
        logging.info(topiclist)
        t = topiclist
        logging.info(t)
        apistart = time.time()
        logger.info(apistart)
        all_articles = newsapi.get_everything(sources=topiclist)
        apiebd = time.time()
        logger.info(apiebd)
        articles = all_articles['articles']
        end = time.time()
        diff = end - start
        logger.info(diff)

        return articles

    def put(self, familyid):
        result = newsclass.getusersources(familyid)
        return result


api.add_resource(GetUsersNews, '/news/user/<familyid>')
api.add_resource(GetNewsSources, '/news/sources')

api.add_resource(NewTasksInternal, '/new/post')
api.add_resource(TaskDetail, '/post/<id>')
api.add_resource(PostList, '/post/list/<id>') #change

api.add_resource(Userlists, '/person/list/<familyid>')  # u
api.add_resource(Userlistposts, '/person/list/posts/<familyid>')  # u
# api.add_resource(UserToDo, '/person/todo/<familyid>')
# api.add_resource(UserToRead, '/person/toread/<familyid>')  # used
# api.add_resource(UserArchived, '/person/archive/<familyid>')  # used
api.add_resource(UsersAll, '/users')  # used
# api.add_resource(ApproveTask, '/app/task/<id>')  # used
# api.add_resource(ApprovalQueue, '/approve/tasks/<familyid>')  # used
api.add_resource(UserRecentlyAdded, '/person/recent/<familyid>')  # used
# api.add_resource(UserTasksMostRead, '/read/tasks/<familyid>')  # refactor to /person/frequent
# api.add_resource(UserTasks, '/tasks/<familyid>')  # used
api.add_resource(UserEmail, '/person/<email>')  # used
api.add_resource(Tags, '/tags')  # used
# api.add_resource(UserPostsByTag, '/tag/<tag>')
api.add_resource(Auth, '/users/authenticate')
# api.add_resource(Register, '/users/register')    # used
api.add_resource(PostTags, '/post/tag')  # used
import sys, os
import time

import sys, os
import time

INTERP = os.path.join(os.environ['HOME'], 'api.mikn.app', 'venv/bin', 'python')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

import logging
import pymysql
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
from sqlalchemy import create_engine, select, MetaData, Table, insert, or_, func
from json import dumps
import simplejson as json
#import requests
from newsapi.newsapi_client import NewsApiClient
from flask import redirect

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
#application.config['SECRET_KEY'] = 'super-secret'
#newsapi = NewsApiClient(api_key='1654f224d44d4dc491f416ef7950a051')

#DB Setup
meta = MetaData(db_connect, reflect=True)
user_prefs_t = meta.tables['userprefs']


@application.route('/')
# @application.route('/implicit/callback')
@cross_origin(origin="*", headers=['Content- Type', 'Authorization'])
def index():
    return 'hello'


class Tags(Resource):
    def get(self):
        conn = db_connect.connect()
        query = conn.execute("select * from tags order by tag desc")
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

    def put(self):
        conn = db_connect.connect()
        tag = request.json['tag']
        query = conn.execute("insert into tags(tag) values('{0}')".format(tag))
        return {'status': 'Tag Added'}


class TopTags(Resource):
    def get(self):
        conn = db_connect.connect()
        query = conn.execute("select tag, tagid, count(tag) as count from taskids a join tags b on a.tagid = b.id  where lower(b.tag) <> 'archive' group by tag, tagid order by 3 desc limit 10")
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class Auth(Resource):
    def post(self):
        conn = db_connect.connect()
	logging.info(request.json)
	password = request.json['password']
	username = request.json['username']
        query = conn.execute("select * from person where password = '{0}' and username = '{1}'".format(password,username))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
	logging.info(result)
	return result[0]

class Register(Resource):
    def post(self):
        conn = db_connect.connect()
        logging.info(request.json)
        password = request.json['password']
        username = request.json['username']
	firstname = request.json['firstName']
	lastname = request.json['lastName']
	email = request.json['email']
        query = conn.execute("insert into person(firstname,lastname,username,password,email) values ('{0}','{1}','{2}','{3}','{4}')".format(firstname,lastname,username,password,email))
        return {'status': 'success'}

class AddTags(Resource):
    def put(self, taskid):
        conn = db_connect.connect()  # connect to database
        tags = request.json['tags']
        query = conn.execute("insert into  taskids(taskid,tagid) values({0},{1})".format(taskid, tags))
        return {'status': 'success'}

class DeleteTags(Resource):
    def delete(self,taskid):
        logging.debug(request.json)
        conn = db_connect.connect()
        tag = request.json['tag']
        query = conn.execute("delete taskids from taskids join tags on tagid = id  where taskid = '{0}' and tag = '{1}'".format(taskid,tag))
        return {'status': 'Tag Added'}



class NewTasksInternal(Resource):
    def post(self):
        logging.info('connecting')
        conn = db_connect.connect()
        logging.info('connected')
        logging.info(request.json)
        print(request.json)
        taskraw = request.json['task']
	logging.info(taskraw)
        task = taskraw.replace("'","")
        logging.info(task)
	logging.info(request)
	ts = time.time()
        familyid = request.json['familyid']
        approved = request.json['approved']
        titleraw = request.json['title']
	title = titleraw.replace("'","")
	summaryraw = request.json['summary']
	summary = summaryraw.replace("'","")
        query = conn.execute("insert into tasks(task,familyid,approved,title,addedts,summary) values('{0}',{1},{2},'{3}',current_timestamp,'{4}')".format(task, familyid, approved,title,summary))
        query2 = conn.execute("select * from tasks where familyid = '{0}' and title = '{1}'".format(familyid,title))
        logging.info(query2)
	result = [dict(zip(tuple(query2.keys()), i)) for i in query2.cursor]
        return jsonify(result)


class NewTasksExternal(Resource):
    def get(self):
        args = request.args
        task = args['task']
        task1 = task.encode('ascii', 'ignore')
        title = args['title']
        ts = time.time()
        title1 = title.encode('ascii', 'ignore')
        conn = db_connect.connect()  # connect to databas
        query = conn.execute("insert into  tasks(task,title,familyid,addedts) values('{0}','{1}','4',current_timestamp )".format(task1, title1))
        return {'status': 'success'}


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

class UserPrefs(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute("select max(case when variable = 1 then prefvalue end) as selectedLeft,max(case when variable = 2 then prefvalue end) as selectedLeftMid, max(case when variable = 3  then prefvalue end) as selectedRightMid,max(case when variable = 4  then prefvalue end) as selectedRight  from userprefs where userid = '{0}'".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return result[0]

    def put(self, familyid):
        logging.info('connecting')
        conn = db_connect.connect()
        logging.info('connected')
        logging.info(request)
        logging.info(request.json)
        conn = db_connect.connect()  # connect to database
        selectedLeft = request.json['selectedLeft']
        selectedRightMid = request.json['selectedRightMid']
        selectedLeftMid = request.json['selectedLeftMid']
        selectedRight = request.json['selectedRight']
        query = conn.execute("update userprefs set prefvalue = '{0}' where variable = '1' and userid = {1}".format(selectedLeft,familyid))
        query2 = conn.execute("update userprefs set prefvalue = '{0}' where variable = '2' and userid = {1}".format(selectedLeftMid,familyid))
        query2 = conn.execute("update userprefs set prefvalue = '{0}' where variable = '3' and userid = {1}".format(selectedRightMid,familyid))
        query2 = conn.execute("update userprefs set prefvalue = '{0}' where variable = '4' and userid = {1}".format(selectedRight,familyid))
        return {'status': 'success'}

class UserTasks(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute("select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null group by a.task,a.id,a.familyid order by lastupdate desc".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class UserToDo(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        param = 'todo'
        query = conn.execute("select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null and c.tag like '{1}' group by a.task,a.id,a.familyid order by lastupdate desc".format(familyid,(param)))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class UserPostsByTag(Resource):
    def get(self, tag):
        conn = db_connect.connect()
        query = conn.execute("select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  = 4 and approved is not null and c.tag = '{0}' group by a.task,a.id,a.familyid order by lastupdate desc".format(tag))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class UserToRead(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute("select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null and lower(c.tag) = 'want to read' group by a.task,a.id,a.familyid order by lastupdate desc".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class UserArchived(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute("select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null and lower(c.tag) = 'archive' group by a.task,a.id,a.familyid order by lastupdate desc".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class UserRecentlyAdded(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute("select a.addedts, a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  = '{0}' and a.addedts > NOW() - INTERVAL 1 WEEK and approved is not null and (b.taskid not in (select taskid from taskids a join tags b on a.tagid = b.id where lower(b.tag) = 'archive') or b.taskid is null)  group by a.task,a.id,a.familyid order by addedts desc limit 5".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class UserTasksMostRead(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute("select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag)  as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null and readcount > 0 and Lower(c.tag) <> 'archive' group by a.task,a.id,a.familyid   order by readcount desc".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)


class ApprovalQueue(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute("select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is null group by a.task,a.id,a.familyid order by lastupdate desc".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class Userlists(Resource):
    def get(self, familyid):
        logging.info('connecting')
	conn = db_connect.connect()
      	query = conn.execute("select GROUP_CONCAT(name) as name from userlists  where familyid  ='{0}'".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
	logging.info(result)
	return result[0]

    def put(self, familyid):
        logging.info('connecting')
        conn = db_connect.connect()
	name = request.json['name']
        query = conn.execute("insert into userlists(familyid,name) values('{0}','{1}')".format(familyid,name))
        return {'status':'success'}

    def delete(self, familyid):
        logging.info('connecting')
        conn = db_connect.connect()
        name = request.json['name']
        query = conn.execute("delete from userlists where name = '{1}' and familyid = '{0}'".format(familyid,name))
        return {'status':'success'}

class Userlistposts(Resource):
    def get(self, familyid):
        conn = db_connect.connect()
        query = conn.execute("select postid as id,c.title as title, a.name as status  from userlists a join userlistposts b on a.id = b.listid join tasks c on b.postid = c.id  where a.familyid  ='{0}'".format(familyid))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

    def put(self,familyid):
        logging.debug(request.json)
	conn = db_connect.connect()
	postid = request.json['id']
	status  = request.json['status']
        query = conn.execute("UPDATE userlistposts SET userlistposts.listid = (select id from userlists where userlists.name = '{0}' and familyid ='{2}' ) where userlistposts.postid = '{1}'".format(status,postid,familyid))
        return {'status':'success'}

    def post(self,familyid):
        logging.info(request.json)
        conn = db_connect.connect()
        postid = request.json['postid']
        name  = request.json['name']
	listid = request.json['listid']
        query = conn.execute("insert into userlistposts(postid,listid,name) values('{1}',(select id from userlists where name = '{0}' and familyid = '{3}'),(select title from tasks where id = '{2}'))".format(listid,postid,name,familyid))
        return {'status':'success'}

    def delete(self,familyid):
        logging.info(request.json)
        conn = db_connect.connect()
        postid = request.json['postid']
        listid = request.json['listid']
        query = conn.execute("delete from userlistposts where postid = '{0}' and listid = (select id from userlists where name = '{1}' and familyid = '{2}') ".format(postid,listid,familyid))
        return {'status':'success'}

class ApproveTask(Resource):
    def put(self, id):
        conn = db_connect.connect()  # connect to database
        query = conn.execute("update tasks set approved  = 1  where id = {0}".format(id))
        return {'status': 'success'}

class PostList(Resource):
    def get(self, id):
        conn = db_connect.connect()
        query = conn.execute("select a.name as listname from userlists a join userlistposts b on a.id = b.listid where b.postid = '{0}'".format(id))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

class TaskDetail(Resource):
    def put(self, id):
        conn = db_connect.connect()  # connect to database
        logging.info(request)
        logging.info(request.json)
	taskraw = request.json['task']
        task = taskraw.replace("'","")
	titleraw = request.json['title']
        title = titleraw.replace("'","")
        summaryraw = request.json['summary']
	summary = summaryraw.replace("'","")
        query = conn.execute("update tasks set task = '{0}', title = '{2}',summary = '{3}'  where id = {1}".format(task, id, title,summary))
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
        query = conn.execute("select a.approved, a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where a.id  ='{0}' group by a.task,a.id,a.familyid".format(id))
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)

    def post(self,id):
        conn = db_connect.connect()
        query = conn.execute("update tasks set readcount = readcount+1 where id = {0}".format(id))
        return {'status': 'read count updated'}

class GetNewsSources(Resource):

    def get(self):
        sources = newsapi.get_sources()
        return sources

    def put(self):
        conn = db_connect.connect()
        source = request.json['source']
        user = request.json['userid']
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
        conn = db_connect.connect()
        q = select([user_prefs_t.c.prefvalue]).where(user_prefs_t.c.variable == 2).where(user_prefs_t.c.userid == familyid)
        query = conn.execute(q)
        results = [dict(zip(tuple(query.keys()), i)) for i in query.cursor.fetchall()]

        if results:
            for i in results:
                topic = i['prefvalue']
                logging.info(topic)
            all_articles = newsapi.get_everything(q=topic)
            articles = all_articles['articles']
            return articles
        else:
            return 'no articles'

api.add_resource(GetUsersNews,'/news/user/<familyid>')
api.add_resource(GetNewsSources,'/news/sources')
api.add_resource(NewTasksInternal, '/new/tasks')
api.add_resource(NewTasksExternal, '/external/tasks')    # used
api.add_resource(TaskDetail, '/task/<id>')
api.add_resource(PostList, '/task/list/<id>')   # used
api.add_resource(UserPrefs, '/person/prefs/<familyid>')   # used
api.add_resource(Userlists, '/person/list/<familyid>')   # u
api.add_resource(Userlistposts, '/person/list/posts/<familyid>')   # u
api.add_resource(UserToDo, '/person/todo/<familyid>')   # used
api.add_resource(UserToRead, '/person/toread/<familyid>')   # used
api.add_resource(UserArchived, '/person/archive/<familyid>')   # used
api.add_resource(UsersAll, '/users')   # used
api.add_resource(ApproveTask, '/app/task/<id>')    # used
api.add_resource(ApprovalQueue, '/approve/tasks/<familyid>')   # used
api.add_resource(UserRecentlyAdded, '/person/recent/<familyid>')   # used
api.add_resource(UserTasksMostRead,'/read/tasks/<familyid>') #refactor to /person/frequent
api.add_resource(UserTasks, '/tasks/<familyid>')   # used
api.add_resource(UserEmail, '/person/<email>')    # used
api.add_resource(Tags, '/tags')    # used
api.add_resource(TopTags, '/top/tags')    # used
api.add_resource(UserPostsByTag, '/tag/<tag>')
api.add_resource(Auth, '/users/authenticate')
api.add_resource(Register, '/users/register')    # used
api.add_resource(AddTags, '/add/tags/<taskid>')    # used
api.add_resource(DeleteTags, '/delete/tags/<taskid>')    # used
import sys, os
import time

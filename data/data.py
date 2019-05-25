import logging
import datetime
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, select, MetaData, Table, insert, or_, func,update

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

db_connect = create_engine('mysql+pymysql://phelper:Lscooter11@mysql.monkeyandjoe.com:3306/phelper')

# DB Setup
meta = MetaData(db_connect, reflect=True)
user_prefs_t = meta.tables['userprefs']
tags_t = meta.tables['tags']
tag_post_t = meta.tables['taskids']
person_t = meta.tables['person']
post_t = meta.tables['tasks']


def dbconnection(q=None):
    conn = db_connect.connect()
    query = conn.execute(q)
    return query


class Lists:

    def __init__(self):
        self.message = 'News'


class News:

    def __init__(self):
        self.message = 'News'

    @staticmethod
    def getusersources(familyid=None):
        q = select([user_prefs_t.c.prefvalue]).where(user_prefs_t.c.variable == 2).where(
            user_prefs_t.c.userid == familyid)
        query = dbconnection(q)
        results = [dict(zip(tuple(query.keys()), i)) for i in query.cursor.fetchall()]
        return jsonify(results)


class Post:

    def __init__(self):
        self.message = 'Post'

    @staticmethod
    def singlepost(id=id,task=None, title=None,summary=None):

        task_p = task.replace("'", "")
        title_p = title.replace("'", "")
        summary_p = summary.replace("'", "")

        upd = update(post_t)\
            .where(id==id)\
            .values(
            title=title_p,
            task=task_p,
            summary=summary_p)

        try:
            query = dbconnection(upd)

            q = select(['*']).where(post_t.c.id == id)

            result = dbconnection(q)

            return jsonify(result)
        except:
            return 'Post Not Updated'

    @staticmethod
    def updreadcount(id=None):

        upd = update(post_t)\
            .where(post_t.c.id ==id).values(
            post_t.c.readcount == post_t.c.readcount+1
        )

        try:
            query = dbconnection(upd)
            return 'updated'
        except:
            return 'not updated'




    @staticmethod
    def postlist(recent=None,familyid=None):
        if recent:
            q =  "select a.addedts, a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  = '{0}' and a.addedts > NOW() - INTERVAL 1 WEEK and approved is not null and (b.taskid not in (select taskid from taskids a join tags b on a.tagid = b.id where lower(b.tag) = 'archive') or b.taskid is null)  group by a.task,a.id,a.familyid order by addedts desc limit 5".format(familyid)
        else:
            q = "select a.summary as summary,a.title,a.task as task,a.id,lastupdate,a.familyid,GROUP_CONCAT(c.tag) as tags  from tasks a left join taskids b on a.id = b.taskid left join tags c on b.tagid = c.id  where familyid  ='{0}' and approved is not null group by a.task,a.id,a.familyid order by lastupdate desc".format(familyid)

        query = dbconnection(q)
        results = [dict(zip(tuple(query.keys()), i)) for i in query.cursor.fetchall()]
        return jsonify(results)

    @staticmethod
    def newpost(task=None,familyid=None,approved=None,title=None,summary=None):

        task_p = task.replace("'", "")
        title_p = title.replace("'", "")
        summary_p = summary.replace("'", "")

        ins = post_t.insert().values(
            task = task_p,
            familyid = familyid,
            approved=approved,
            title = title_p,
            summary = summary_p,
            addedts = datetime.datetime.now()
        )

        try:
            query = dbconnection(ins)

            q = select(['*']).where(post_t.c.title == title_p)

            result = dbconnection(q)

            return jsonify(result)
        except:
            return 'Post Not Added'

    @staticmethod
    def manageposttag(add=None, delete=None, postid=None, tagid=None):

        tagtable = Table('taskids', meta)

        if add:

            ins = tagtable.insert().values(
                taskid=postid,
                tagid=tagid
            )

            try:

                query = dbconnection(ins)
                return 'Tag Added to Post'

            except:

                return 'Tag Not Added to post'
        else:
            delete = tagtable.delete().where(
                tagtable.c.taskid == postid
            ).where(tagtable.c.tag == tagid)

            try:
                query = dbconnection(delete)
                return 'Tag Removed from Post'
            except:
                return 'Tag Not Removed From post'


class Tags:

    def __init__(self):
        self.message = 'Tags'

    @staticmethod
    def addtags(tag=None):
        views = Table('tags', meta)

        ins = views.insert().values(
            tag=tag
        )

        try:

            query = dbconnection(ins)
            return 'Tag Added'

        except:

            return 'Tag Not Added'

    @staticmethod
    def gettags(top=None):

        if top:
            join_obj_tags = tags_t \
                .join(tag_post_t, tags_t.c.id == tag_post_t.c.tagid)
            listlimit = 10

            q = select([tags_t.c.tag, tags_t.c.id, func.count(tag_post_t.c.tagid)]) \
                .select_from(join_obj_tags) \
                .group_by(tags_t.c.tag, tags_t.c.id) \
                .order_by(func.count(tag_post_t.c.tagid).desc()) \
                .limit(listlimit)

        else:
            q = select([tags_t.c.id, tags_t.c.tag])

        query = dbconnection(q)
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return jsonify(result)


class User:

    def __init__(self):
        self.message = 'User'

    #refactor vue to not use this but use state
    @staticmethod
    def userid(email=None):
        q = select([person_t.c.familyid]).where(person_t.c.email == email)
        query = dbconnection(q)
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        return result[0]

    @staticmethod
    def authorizeuser(new=None, firstname=None, lastname=None, email=None, password=None, username=None):

        if new:
            personadd = Table('person', meta)

            ins = personadd.insert().values(
                firstname=firstname,
                lastname=lastname,
                username=username,
                password=password,
                email=email
            )

            try:

                query = dbconnection(ins)
                return 'User Added'

            except:

                return 'User Not Added'

        else:
            q = select(['*']).where(person_t.c.password == password).where(person_t.c.username == username)
            query = dbconnection(q)
            results = [dict(zip(tuple(query.keys()), i)) for i in query.cursor.fetchall()]
            return results[0]



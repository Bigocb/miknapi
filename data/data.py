import logging
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, select, MetaData, Table, insert, or_, func

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

#DB Setup
meta = MetaData(db_connect, reflect=True)
user_prefs_t = meta.tables['userprefs']
tags_t = meta.tables['tags']
tag_post_t = meta.tables['taskids']
person_t = meta.tables['person']


def dbconnection(q=None):
    conn = db_connect.connect()
    query = conn.execute(q)
    return query


class News:

    def __init__(self):
        self.message = 'News'

    @staticmethod
    def getusersources(familyid=None):
        q = select([user_prefs_t.c.prefvalue]).where(user_prefs_t.c.variable == 2).where(user_prefs_t.c.userid == familyid)
        query = dbconnection(q)
        results = [dict(zip(tuple(query.keys()), i)) for i in query.cursor.fetchall()]
        return jsonify(results)


class Post:

    def __init__(self):
        self.message = 'Post'

    @staticmethod
    def manageposttag(add=None,delete=None,postid = None, tagid=None):

        if add:
        
            tagtable = Table('taskids', meta)

            ins = tagtable.insert().values(
                taskid=postid,
                tagid=tagid
            )

            try:

                query = dbconnection(ins)
                return 'Tag Added to Post'

            except:

                return 'Tag Not Added to post'


class Tags:

    def __init__(self):
        self.message = 'Tags'

    @staticmethod
    def addtags(tag = None):
        views = Table('tags', meta)

        ins = views.insert().values(
                tag = tag
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








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


def dbConnection(q=None):
    conn = db_connect.connect()
    query = conn.execute(q)
    return query


def getUserPrefs(familyid=None):
    q = select([user_prefs_t.c.prefvalue]).where(user_prefs_t.c.variable == 2).where(user_prefs_t.c.userid == familyid)
    query = dbConnection(q)
    results = [dict(zip(tuple(query.keys()), i)) for i in query.cursor.fetchall()]
    return jsonify(results)

def getTags():
    q = select([tags_t.c.id,tags_t.c.tag])
    query = dbConnection(q)
    result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
    return jsonify(result)




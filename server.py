#!/usr/bin/python
# -*- coding: utf-8 -*-  

import web
import traceback
import json,decimal
import sys,os,dbconf
from orator.support.collection import Collection
from orator import DatabaseManager
reload(sys)
sys.setdefaultencoding('utf8')

urls = (
    '/query.json', 'QueryProvider',
    '/table.json', 'TableMetaProvider',
    '/update.json','UpdateProvider'
)
app = web.application(urls, globals())
config = dbconf.db_conf
     
def load_sqla(handler):
    web.ctx.orm = DatabaseManager(config)
    try:
        web.ctx.orm.begin_transaction()
        return handler()
    except web.HTTPError:
       web.ctx.orm.commit()
       raise
    except:
        web.ctx.orm.rollback()
        raise
    finally:
        web.ctx.orm.commit()
        # If the above alone doesn't work, uncomment 
        # the following line:
        #web.ctx.orm.expunge_all()


app.add_processor(load_sqla)
def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, Collection):
        return obj.all()
    return str(obj)

class BaseProvider:
    def POST(self):
        try:
            data=None
            if len(web.data())>0:
                data = json.loads(web.data())
            return json.dumps(self.run(data),default=decimal_default)
        except Exception,e:
            traceback.print_exc()
            return json.dumps({'code':-1,'message':str(e)})
    def GET(self,param):
        return param

class DbCall:
    def __init__(self,db):
        self.db=db
    def getTableDesc(self,table):
        dataset = self.db.select("show create table "+ table)
        content=dataset[0]["Create Table"]
        return content
    def getTableCols(self,table):
        dataset=self.db.select("desc "+ table)
        cols=[i['FIELD'] for i in dataset]
        news_cols = list(set(cols))
        news_cols.sort(key=cols.index)
        return news_cols
    def getTables(self):
        dataset = self.db.select('show tables')
        return [x['NAME'] for x in dataset]
    def updateById(self,table,id,col,val):
        upMap={}
        upMap[col]=val
        try:
            col=self.getTableCols(table)
            self.db.table(table).where(col[0],id).update(upMap)
        except:
            return False
        return True
class QueryProvider(BaseProvider):
    def run(self,data):
        result={'code':-1}
        db=web.ctx.orm
        sqlst=data['query'].lower()
        order_by='id'
        order_des='desc'
        if 'order by ' in sqlst:return {'code':-3,'message':'不能做排序'}
        if 'limit ' in sqlst:return {'code':-2,'message':'不能做位置筛选'}
        if data and ('table' in data) and ('query' in data):
            dbcall=DbCall(db)
            if data['query']=='':data['query']='1=1'
            cols=dbcall.getTableCols(data['table'])
            if 'id' not in cols:order_by=cols[0]
            if 'order_by' in data and data['order_by'] in cols: order_by=data['order_by']
            if order_by not in cols:order_by=cols[0]
            if 'order_des' in data and data['order_des'] in ['desc','asc']: order_des=data['order_by']
            sql=db.table(data['table']).where_raw(data['query']).order_by(order_by,order_des).group_by(cols[0])
            c=sql.count()
            d=sql.limit(15).get()
            result={'code':0,'result':{"data":d,"count":c}}
        return result
class TableMetaProvider(BaseProvider):
    def run(self,data):
        result={'code':-1}
        db=web.ctx.orm
        dbcall=DbCall(db)
        if data and ('type' in data) and data['type']=='meta' and ('table' in data) and data['table']!='':
            content=dbcall.getTableDesc(data['table'])
            cols=dbcall.getTableCols(data['table'])
            order_by='id'
            if 'id' not in cols:order_by=cols[0]
            sql=db.table(data['table']).order_by(order_by,'desc')
            result={'code':0,'result':{"data":content.decode('utf8').replace('\n','<br/>'),"count":db.table(data['table']).count(),"cols":cols,"content":sql.limit(15).get()}}
        else:
            result ={'code':0,'result':dbcall.getTables()}
        return result
class UpdateProvider(BaseProvider):
    def run(self,data):
        result={'code':-1}
        db=web.ctx.orm
        if data and ('table' in data) and data['table']!='' and ('id' in data) and data['id']!='' and ('col' in data) and data['col']!='':
            dbcall=DbCall(db)
            val=''
            if ('val' in data) and data['val']!='':
                val=data['val']
            if dbcall.updateById(data['table'],data['id'],data['col'],data['val']):
                result ={'code':0}
        return result
if __name__ == "__main__":
    app.run()

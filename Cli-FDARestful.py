from flask import Flask, url_for ,jsonify
from flask_restful import Resource, Api, reqparse, abort

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import *


# 1. handle request Error

TODOS = {
    'GetClinical_FromGene': {'url': 'ip:5000/api/getClinicalFDA/<gene_name>'},
    'GetFDA_FromDrug': {'url': 'ip:5000/api/getFDA/<drug_name>'},
}

errors = {
    'URLNotFound': {
        'message': "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again..",
        'status': 404,
    },
    'ResourceDoesNotExist': {
        'message': "A resource with that ID no longer exists.",
        'status': 410,
        'extra': "Any extra information you want.",
    },
}

app = Flask(__name__)
api = Api(app , catch_all_404s=True) #http://flask-restful.readthedocs.io/en/0.3.5/extending.html
# MySQL configurations
engine = create_engine('mysql://root:@localhost:3306/clintrialsgov_out', echo=False)
Session = sessionmaker(bind=engine)
db_session = Session()
Base = declarative_base()


def abort_if_resource_doesnt_exist(key):
    abort(404, status=404, message="Todo {} doesn't exist".format(key))

class GetFDA_FromDrug(Resource):
    def get(self, drug_name):
        _key_drug_name = "%" + drug_name + "%"
        _app_no = []

        _FDA = []
        _temp_FDA_Product = []
        _FDA_appdoc = []
        _FDA_actionDate = []
        #distinct
        for row in db_session.query(FDAProduct.ApplNo) \
                .filter(FDAProduct.DrugName.ilike(_key_drug_name)).distinct():
            _app_no.append(row.ApplNo)

        for row in db_session.query(FDAProduct.ApplNo, FDAProduct.ProductNo, FDAProduct.Form, FDAProduct.Dosage,
                                    FDAProduct.DrugName, FDAProduct.Activeingred) \
                .filter(FDAProduct.ApplNo.in_(_app_no)):
            _temp_FDA_Product.append(row._asdict())


        for ApplNo in _app_no:
            _temp_group_Interventions = []
            for item in _temp_FDA_Product:
                for key, value in item.items():
                    if ( key == 'ApplNo' and ApplNo == value):
                        _temp_group_Interventions.append(item)
            d = dict(ApplNo=ApplNo)
            d['product']=_temp_group_Interventions
            _FDA.append(d)


        _temp_FDA_AppDoc = []
        for row in db_session.query(FDAAppdoc.ApplNo, FDAAppdoc.DocURL, FDAAppdoc.DocDate, FDAAppdoc.ActionType,)\
                .filter(or_(*[FDAAppdoc.ApplNo.like("%"+name) for name in _app_no])):
            _temp_FDA_AppDoc.append(row._asdict())

        for ApplNo in _app_no:
            _temp_group_Interventions = []
            for item in _temp_FDA_AppDoc:
                for key, value in item.items():
                    if (key == 'ApplNo' and ApplNo == value):
                        _temp_group_Interventions.append(item)
            d = dict(ApplNo=ApplNo)
            d['appDoc'] = _temp_group_Interventions
            _FDA_appdoc.append(d)

        _temp_FDA_actionDate = []
        for row in db_session.query(FDARegActionDate.ApplNo, FDARegActionDate.ActionDate, FDARegActionDate.DocType,
                                    ).filter(FDARegActionDate.ApplNo.in_(_app_no)):
            _temp_FDA_actionDate.append(row._asdict())

        for ApplNo in _app_no:
            _temp_group = []
            for item in _temp_FDA_actionDate:
                for key, value in item.items():
                    if (key == 'ApplNo' and ApplNo == value):
                        _temp_group.append(item)
            d = dict(ApplNo=ApplNo)
            d['actionDate'] = _temp_group
            _FDA_actionDate.append(d)

        return jsonify({'status': 'success',
                'request': drug_name,
                'FDA_Product': _FDA,
                'FDA_appDoc': _FDA_appdoc,
                'FDA_actionDate': _FDA_actionDate,
                })

class GetClinical_FromGene(Resource):
    def get(self,gene_name):
        _key_gene_name = "%"+gene_name+"%"
        _nct_id = []
        _clinicalTrial_Study =[]

        for row in db_session.query(ClinicalStudy.nct_id ,ClinicalStudy.brief_title,ClinicalStudy.brief_summary ,ClinicalStudy.detailed_description, ClinicalStudy.criteria).filter(ClinicalStudy.brief_title.like(_key_gene_name)):
            # print(row.nct_id)
            _clinicalTrial_Study.append(row._asdict())
            _nct_id.append(row.nct_id)

        #for item in _clinicalTrial_Study:
        #    for key, value in item.items():
        #        print(key, 'corresponds to', value)

        _temp_clinicalTrial_Interventions = []
        for row in  db_session.query(Interventions.intervention_id ,Interventions.nct_id ,Interventions.intervention_name,Interventions.intervention_type ,Interventions.description).filter(Interventions.nct_id.in_(_nct_id)):
            _temp_clinicalTrial_Interventions.append(row._asdict())

        _clinicalTrial_Interventions=[]
        for nct_id in _nct_id:
            _temp_group_Interventions = []
            for item in _temp_clinicalTrial_Interventions:
                for key, value in item.items():
                    if ( key == 'nct_id' and nct_id == value):
                        _temp_group_Interventions.append(item)
            d = dict(nct_id=nct_id)
            d['interventions']=_temp_group_Interventions
            _clinicalTrial_Interventions.append(d)

        _temp_clinicalTrial_Conditions = []
        for row in db_session.query(Conditions.NCT_ID, Conditions.CONDITIONS).filter(Conditions.NCT_ID.in_(_nct_id)):
            _temp_clinicalTrial_Conditions.append(row._asdict())

        _clinicalTrial_Conditions=[]
        for nct_id in _nct_id:
            _temp_group_Conditions = []
            for item in _temp_clinicalTrial_Conditions:
                for key, value in item.items():
                    if ( key == 'NCT_ID' and nct_id == value):
                        _temp_group_Conditions.append(item)
            d = dict(nct_id=nct_id)
            d['conditions']=_temp_group_Conditions
            _clinicalTrial_Conditions.append(d)

        return jsonify({'status': 'success',
                'request' :gene_name,
                'clinicalTrial_Interventions':_clinicalTrial_Interventions,
                'clinicalTrial_Study':_clinicalTrial_Study ,
                'clinicalTrial_Conditions':_clinicalTrial_Conditions,
                })

class ClinicalStudy(Base):
        __table__ = Table('clinical_study', Base.metadata,
                    autoload=True, autoload_with=engine)

class Interventions(Base):
    __table__ = Table('interventions', Base.metadata,
                      autoload=True, autoload_with=engine)

class Conditions(Base):
    __table__ = Table('conditions', Base.metadata,
                      autoload=True, autoload_with=engine)



class FDAProduct(Base):
    __table__ = Table('fda_product', Base.metadata,
                      autoload=True, autoload_with=engine)

class FDARegActionDate(Base):
    __table__ = Table('fda_reg_action_date', Base.metadata,
                      autoload=True, autoload_with=engine)

class FDAAppdoc(Base):
    __table__ = Table('fda_appdoc', Base.metadata,
                      autoload=True, autoload_with=engine)



# TodoList
# shows a list of all todos, and lets you POST to add new tasks
class TodoList(Resource):
    def get(self):
        return TODOS


api.add_resource(TodoList, '/','/ToDoList')

api.add_resource(GetClinical_FromGene, '/api/getClinical/<string:gene_name>' , endpoint= 'getClinical')
api.add_resource(GetFDA_FromDrug, '/api/getFDA/<string:drug_name>' , endpoint= 'getFDA')



if __name__ == '__main__':
    app.run(debug=True)


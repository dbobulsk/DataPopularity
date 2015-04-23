__author__ = 'mikhail91'

from flask import Flask, request, redirect, url_for, flash, send_from_directory
from flask.ext.restful import reqparse, abort, Api, Resource
import werkzeug

from DataPopularity import DataPopularityEstimator, DataIntensityPredictor, DataPlacementOptimizer
import rep
import numpy as np
import pandas as pd
import re
import os
import ast

ALLOWED_EXTENSIONS = set(['csv'])

#
app = Flask(__name__)
api = Api(app)

cur_dir = os.getcwd()
data_popularity_data = cur_dir + '/data_dir' + '/'

#Get session_id
class GetSessionId(Resource):
    session_id=''

    def get(self):
        return 'Use POST to generate new session_id.'

    def post(self):
        self.session_id = str(np.random.randint(low=1, high=10000))
        while os.path.exists(data_popularity_data + self.session_id):
            self.session_id = str(np.random.randint(low=1, high=10000))
        os.makedirs(data_popularity_data + self.session_id)
        return 'Your NEW session_id = '+self.session_id

    def put(self):
        return 'Use POST to generate new session_id.'

    def delete(self):
        return 'Your can not delete your session_is.'

#Data Uploading
class DataUpload(Resource):

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

    def get(self, session_id):
        return 'Your data saved in directory /' + data_popularity_data + session_id + '/' + 'data.csv'

    def post(self, session_id):
        file = request.files['file']
        if file and self.allowed_file(file.filename):
            data_path = data_popularity_data + session_id + '/' + 'data.csv'
            file.save(data_path)
        else:
            return 'Please, send data file in .csv format.'
        return 'Your data saved in directory /' + data_popularity_data + session_id + '/' + 'data.csv'

    def put(self, session_id):
        file = request.files['file']
        if file and self.allowed_file(file.filename):
            data_path = data_popularity_data+ session_id + '/' + 'data.csv'
            file.save(data_path)
        return 'Your data saved in directory /' + data_popularity_data + session_id + '/' + 'data.csv'

    def delete(self):
        pass


#DataPopularity
class DataPopularityApi(Resource):
    def take_params(self, req):
        get_params = ast.literal_eval(req)
        params = {}
        params['nb_of_weeks'] = get_params['nb_of_weeks'] if get_params.has_key('nb_of_weeks') else 104
        params['q'] = get_params['q'] if get_params.has_key('q') else None
        params['set_replicas'] = get_params['set_replicas'] if get_params.has_key('set_replicas') else 'auto'
        params['c_disk'] = get_params['c_disk'] if get_params.has_key('c_disk') else 100
        params['c_tape'] = get_params['c_tape'] if get_params.has_key('c_tape') else 1
        params['c_miss'] = get_params['c_miss'] if get_params.has_key('c_miss') else 2000
        params['alpha'] = get_params['alpha'] if get_params.has_key('alpha') else 1
        params['max_replicas'] = get_params['max_replicas'] if get_params.has_key('max_replicas') else 4
        params['method'] = get_params['method'] if get_params.has_key('method') else 'opti'
        params['pop_cut'] = get_params['pop_cut'] if get_params.has_key('pop_cut') else -1
        return params

    def get(self, session_id):
        return 'Files data.csv, popularity.csv, prediction.csv, report.csv and opti_report.csv ' \
               'are in your working directory /' + data_popularity_data +session_id

    def post(self, session_id):
        params = self.take_params(request.form['params'])
        data_folder = data_popularity_data + session_id
        data_path = data_folder + '/data.csv'
        data = pd.read_csv(data_path)

        estimator = DataPopularityEstimator(data=data, nb_of_weeks=params['nb_of_weeks'])
        estimator.train()
        popularity_report = estimator.get_popularity()
        popularity_report.to_csv(data_folder + '/popularity.csv')


        predictor = DataIntensityPredictor(data=data, nb_of_weeks=params['nb_of_weeks'])
        prediction_report = predictor.predict(zero_one_scale=False)
        prediction_report.to_csv(data_folder + '/prediction.csv')

        optimizer = DataPlacementOptimizer(popularity_report, prediction_report, data=data)
        if params['method']=='opti':
            opti_report = optimizer.opti_placement(q=params['q'], set_replicas=params['set_replicas'],\
                                                   c_disk=params['c_disk'], \
                                                   c_tape=params['c_tape'], \
                                                   c_miss=params['c_miss'], \
                                                   alpha=params['alpha'], \
                                                   max_replicas=params['max_replicas'])
            opti_report.to_csv(data_folder + '/opti_report.csv')
            return 'Data Popularity report generated in /'+data_folder + '/opti_report.csv'
        else :
            report = optimizer.get_report(q=params['q'], pop_cut=params['pop_cut'], set_replicas=params['set_replicas'],\
                                                   alpha=params['alpha'], \
                                                   max_replicas=params['max_replicas'])
            report.to_csv(data_folder + '/report.csv')
            return 'Data Popularity report generated in /'+data_folder + '/report.csv'

    def put(self, session_id):
        params = self.take_params(request.form['params'])
        data_folder = data_popularity_data + session_id
        data_path = data_folder + '/data.csv'
        data = pd.read_csv(data_path)

        popularity_report = pd.read_csv(data_folder + '/popularity.csv')
        prediction_report = pd.read_csv(data_folder + '/prediction.csv')

        optimizer = DataPlacementOptimizer(popularity_report, prediction_report, data=data)
        if params['method']=='opti':
            opti_report = optimizer.opti_placement(q=params['q'], set_replicas=params['set_replicas'],\
                                                   c_disk=params['c_disk'], \
                                                   c_tape=params['c_tape'], \
                                                   c_miss=params['c_miss'], \
                                                   alpha=params['alpha'], \
                                                   max_replicas=params['max_replicas'])
            opti_report.to_csv(data_folder + '/opti_report.csv')
            return 'Data Popularity report generated in /'+data_folder + '/opti_report.csv'
        else :
            report = optimizer.get_report(q=params['q'], pop_cut=params['pop_cut'], \
                                          set_replicas=params['set_replicas'],\
                                                   alpha=params['alpha'], \
                                                   max_replicas=params['max_replicas'])
            report.to_csv(data_folder + '/report.csv')
            return 'Data Popularity report generated in /'+data_folder + '/report.csv'

    def delete(self, session_id):
        pass


class DataDownload(Resource):
     def get(self, session_id, filename):
         data_folder = data_popularity_data + session_id
         return send_from_directory(data_folder, filename=filename, as_attachment=True)




#Add API
api.add_resource(GetSessionId, '/')
api.add_resource(DataUpload, '/<string:session_id>/Upload')
api.add_resource(DataPopularityApi, '/<string:session_id>/DataPopularityApi')
api.add_resource(DataDownload, '/<string:session_id>/Download/<string:filename>')


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
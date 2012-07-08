from .app import app, mongo

from flask import render_template, request
from flask.ext.pymongo import ASCENDING


@app.route('/case/<path:caseid>', methods=['GET'])
def case(caseid):
    case = mongo.db.cases.find_one({'_id': caseid})
    violation = mongo.db.violation_codes.find_one({'_id': case['violation']})
    cases_on_page = mongo.db.cases.find({'book': case['book'],
                                         'page': case['page'],
                                         },
                                        sort=[('_id', ASCENDING)],
                                        )
    job = mongo.db.jobs.find_one({'_id': case['load_job_id']})
    app.logger.debug('args: %r', request.args)
    user_debug = bool(request.args.get('debug', False))
    return render_template('case.html',
                           case=case,
                           violation=violation,
                           cases_on_page=cases_on_page,
                           debug=(app.debug or user_debug),
                           job=job,
                           )

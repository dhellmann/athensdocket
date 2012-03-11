from pymongo import Connection


class DBFactory(object):

    def __init__(self, dbname):
        self.dbname = dbname

    @property
    def conn(self):
        return Connection()

    def __call__(self):
        return getattr(self.conn, self.dbname)


class ErrorHandler(object):

    def __init__(self, db_factory, job_id, filename):
        self.db_factory = db_factory
        self.job_id = job_id
        self.filename = filename

    @property
    def db(self):
        return self.db_factory()

    def __call__(self, message):
        self.db.errors.insert(
            {'job_id': self.job_id,
             'filename': self.filename,
             'message': message,
             })

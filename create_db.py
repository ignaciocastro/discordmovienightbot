import config
import pymongo

config.collection.drop()

print('collection dropped')

test_movie = {"imdbID": 'tt1234567',
              "Title": 'Test',
              "Released": '1999',
              "rtScore": '9.0',
              "Runtime": '120',
              "Plot": 'Cool movie',
              "submitter": 'Me',
              "viewed": False,
              "viewedDate": None,
              "Poster": "http://google.com/"}
test = config.collection.insert_one(test_movie)
print(test.inserted_id)

dblist = config.cluster.list_database_names()
print(dblist)
collist = config.db.list_collection_names()
print(collist)
for x in config.collection.find():
    print(x)
print('test movie created')
config.collection.delete_one({"imdbID": "tt1234567"})
for x in config.collection.find():
    print(x)
print('test movie deleted')

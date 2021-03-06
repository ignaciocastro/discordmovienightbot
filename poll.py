# poll.py
import config
import random


def create_poll(num_minutes):
    unviewed_movies = []
    all_movies = config.collection.find({"viewed": False})

    for movie in config.collection.find({"viewed": False}):
        current_movie_str = str(movie['Title']) + \
            " (https://imdb.com/title/" + str(movie['imdbID']) + \
            "), submitted by " + str(movie['submitter']) + "\n"
        unviewed_movies.append(current_movie_str)

    poll_list = unviewed_movies

    poll_list_with_indexes = []

    if len(unviewed_movies) > 10:
        poll_list = random.sample(unviewed_movies, k=10)

    for index, movie in enumerate(poll_list, start=1):
        current_movie_str = str(index) + ") " + movie
        poll_list_with_indexes.append(current_movie_str)

    poll_list_str = ""

    for movie in poll_list_with_indexes:
        poll_list_str += movie + "\n"

    return poll_list_str


def tiebreak(movies):
    poll_list_with_indexes = []
    for index, movie in enumerate(movies, start=1):
        current_movie_str = str(index) + ") " + movie
        poll_list_with_indexes.append(current_movie_str)
    poll_list_str = ""
    for movie in poll_list_with_indexes:
        poll_list_str += movie + "\n"

    return poll_list_str


def poll_to_dict(poll_str):
    poll_dict = {}
    movie_list = list(filter(bool, poll_str.splitlines()))
    for movie in movie_list:
        poll_dict[str(movie.split(')')[0])] = {'Title':
                                               movie.split('(')[0].split(')')[
                                                   1].strip(),
                                               'votes': 0}

    return poll_dict


def poll_to_dict_for_voting(poll_str):
    poll_dict = {}
    movie_list = list(filter(bool, poll_str.splitlines()))
    for movie in movie_list:
        print(movie)
        poll_dict[str(movie.split(')')[0])] = {'Title':
                                               movie.split('(')[0].split(')')[
                                                   1].strip(),
                                               'link':
                                               movie.split('(')[1].split(')')[
                                                   0].strip(),
                                               'submitter': movie.split('by')[
                                                   1].strip()}
    print(poll_dict)

    return poll_dict

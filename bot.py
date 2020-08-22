# bot.py
import config
import datetime
from datetime import datetime
import os
import discord
import asyncio
from dotenv import load_dotenv
from discord.ext import commands, tasks
from update_list import add_movie_id, check_movie_id_in_list
from update_list import check_movie_id_in_any_list, remove_movie_id
from update_list import add_movie_title, check_movie_title_in_list
from update_list import check_movie_title_in_any_list, remove_movie_title
from update_list import search_movie_title
from show_list import show_list
from set_viewed import set_viewed_by_id, set_viewed_by_title
from poll import create_poll, poll_to_dict, tiebreak

load_dotenv()

client = discord.Client()

bot = commands.Bot(command_prefix='--')

"""server = client.get_guild(config.SERVER)
print(server)
channel = client.get_channel(config.CHANNEL)
print(channel)
print(bot.get_all_channels())
print(client.get_all_channels())

for guild in client.guilds:

    print(guild)"""

current_poll_dict = {}

poll_running = False

users_who_voted = []


@bot.command(name='toggleautoview', help='Toggle autoview of movies after poll is done.')
async def toggleautoview(ctx):
    config.autoview = not config.autoview
    response = f"Autoview has been set to {config.autoview}"
    await ctx.send("```" + response + "```")


@tasks.loop(hours=168.0)
async def autopoll():
    print('in loop')
    print('running autopoll')
    channel = bot.get_channel(int(config.CHANNEL))
    global poll_running
    global users_who_voted
    poll_running = True
    num_minutes = 1440
    ctx = channel
    response = f'Setting a poll for {num_minutes} minutes'

    # send initial message
    response += "\n @everyone poll is starting, use vote command to vote"
    await ctx.send(response)

    # get all the movies of the poll
    response = create_poll(num_minutes)

    # call function to convert str to dict
    global current_poll_dict
    current_poll_dict = poll_to_dict(response)

    # send poll
    message = await ctx.send("```" + response + "```")

    # send results on poll end
    poll_time_seconds = num_minutes * 60
    print(poll_time_seconds)
    await asyncio.sleep(poll_time_seconds)

    print("poll is done")
    poll_running = False
    users_who_voted.clear()

    # get max value
    reformatted_dict = {}
    for key, val in current_poll_dict.items():
        reformatted_dict[val['title']] = val['votes']
    most_votes = max(reformatted_dict.values())
    keys = [key for key, value in reformatted_dict.items() if value == most_votes]
    import random
    if len(keys) > 1:
        emojis = ['1\u20E3', '2\u20E3', '3\u20E3', '4\u20E3', '5\u20E3',
                '6\u20E3', '7\u20E3', '8\u20E3', '9\u20E3', '\U0001f51f']
        emojis = emojis[:len(keys)]
        # add emojis
        tiebreak_message = f"There was a tie of {most_votes} votes between {len(keys)} movies \n" + \
            "@everyone Please vote for the tiebreaker. You have 5 minutes. \n" + \
            "and if you tie again, I'll pick one myself :)"

        # Create tiebreak poll
        await ctx.send(tiebreak_message)
        tiebreak_poll = tiebreak(keys)
        tiebreak_poll_message = await ctx.send("```" + tiebreak_poll + "```")
        tiebreak_poll_message_id = tiebreak_poll_message.id
        for emoji in emojis:
            await tiebreak_poll_message.add_reaction(emoji)
        await asyncio.sleep(config.tiebreak_num_seconds)
        tiebreak_poll_message = await ctx.fetch_message(tiebreak_poll_message_id)
        # Count tiebreak reactions
        tiebreak_reactions = {}
        for reaction in tiebreak_poll_message.reactions:
            tiebreak_reactions[reaction.emoji] = reaction.count
        print(tiebreak_reactions)
        most_votes = max(tiebreak_reactions.values())
        tiebreak_keys = [key for key, value in tiebreak_reactions.items() if value == most_votes]
        # Tied again, just pick a random from the tiebreak poll
        if len(tiebreak_keys) > 1:
            winner = random.choice(keys)
            poll_results = "Tiebreak is now completed \n" + \
                f"There was another tie zzz \n" + \
                f"Since you can't decide, I've decided that the winner is {winner}"
        else:
            winner = keys[emojis.index(tiebreak_keys[0])]
            poll_results = f"Tie is broken, and the winner is {winner}!"

    else:
        winner = keys[0]
        poll_results = "Poll is now completed \n" + f"Winner is {winner}" + \
        f" with {most_votes} votes!"

    # if autoview on, set winner to viewed
    if config.autoview:
        config.collection.find_one_and_update({"title": winner}, {'$set': {'viewed': True, 'viewedDate': datetime.datetime.utcnow()}})

    await ctx.send("```" + poll_results + "```")


@autopoll.before_loop
async def wait_to_start_autopoll():
    print('before loop')
    print(config.autopoll_schedule, datetime.now().replace(microsecond=0))
    print(datetime.now().replace(microsecond=0) >= config.autopoll_schedule)
    time_diff = config.autopoll_schedule - datetime.now().replace(microsecond=0)
    print(time_diff.total_seconds())
    if time_diff.total_seconds() > 0:
        await asyncio.sleep(time_diff.total_seconds())


@bot.command(name='poll', help='Select 10 random movies and create a poll. ' +
             'Default time 1440 min (24 hours)')
async def poll(ctx, num_minutes: int = 1440):
    print('starting poll')
    global poll_running
    global users_who_voted
    poll_running = True
    if num_minutes == 1:
        response = f'Setting a poll for {num_minutes} minute'
    else:
        response = f'Setting a poll for {num_minutes} minutes'

    # send initial message
    response += "\n @everyone poll is starting, use vote command to vote"
    await ctx.send(response)

    # get all the movies of the poll
    response = create_poll(num_minutes)

    # call function to convert str to dict
    global current_poll_dict
    current_poll_dict = poll_to_dict(response)

    # send poll
    message = await ctx.send("```" + response + "```")

    # send results on poll end
    poll_time_seconds = num_minutes * 60
    print(poll_time_seconds)
    await asyncio.sleep(poll_time_seconds)

    print("poll is done")
    poll_running = False
    users_who_voted.clear()

    # get max value
    reformatted_dict = {}
    for key, val in current_poll_dict.items():
        reformatted_dict[val['title']] = val['votes']
    most_votes = max(reformatted_dict.values())
    keys = [key for key, value in reformatted_dict.items() if value == most_votes]
    import random
    if len(keys) > 1:
        emojis = ['1\u20E3', '2\u20E3', '3\u20E3', '4\u20E3', '5\u20E3',
                  '6\u20E3', '7\u20E3', '8\u20E3', '9\u20E3', '\U0001f51f']
        emojis = emojis[:len(keys)]
        # add emojis
        tiebreak_message = f"There was a tie of {most_votes} votes between {len(keys)} movies \n" + \
            "@everyone Please vote for the tiebreaker. You have 5 minutes. \n" + \
            "and if you tie again, I'll pick one myself :)"

        # Create tiebreak poll
        await ctx.send(tiebreak_message)
        tiebreak_poll = tiebreak(keys)
        tiebreak_poll_message = await ctx.send("```" + tiebreak_poll + "```")
        tiebreak_poll_message_id = tiebreak_poll_message.id
        for emoji in emojis:
            await tiebreak_poll_message.add_reaction(emoji)
        await asyncio.sleep(config.tiebreak_num_seconds)
        tiebreak_poll_message = await ctx.fetch_message(tiebreak_poll_message_id)
        # Count tiebreak reactions
        tiebreak_reactions = {}
        for reaction in tiebreak_poll_message.reactions:
            tiebreak_reactions[reaction.emoji] = reaction.count
        print(tiebreak_reactions)
        most_votes = max(tiebreak_reactions.values())
        tiebreak_keys = [key for key, value in tiebreak_reactions.items() if value == most_votes]
        # Tied again, just pick a random from the tiebreak poll
        if len(tiebreak_keys) > 1:
            winner = random.choice(keys)
            poll_results = "Tiebreak is now completed \n" + \
                f"There was another tie zzz \n" + \
                f"Since you can't decide, I've decided that the winner is {winner}"
        else:
            winner = keys[emojis.index(tiebreak_keys[0])]
            poll_results = f"Tie is broken, and the winner is {winner}!"

    else:
        winner = keys[0]
        poll_results = "Poll is now completed \n" + f"Winner is {winner}" + \
        f" with {most_votes} votes!"

    # if autoview on, set winner to viewed
    if config.autoview:
        config.collection.find_one_and_update({"title": winner}, {'$set': {'viewed': True, 'viewedDate': datetime.datetime.utcnow()}})

    await ctx.send("```" + poll_results + "```")


@bot.command(name='schedule', help='Schedule poll')
async def schedule(ctx, datetime_str: str):
    from dateutil.parser import parse
    datetime = parse(datetime_str)
    message = f"Poll is scheduled for {datetime}"
    await ctx.send("```" + message + "```")
    config.autopoll_schedule = datetime
    print(config.autopoll_schedule)
    print('autopoll start')
    autopoll.start()


@bot.command(name='vote', help='Cast your votes in order from first to third' +
             ' pick. Use the number labels generated by the poll.')
async def vote(ctx, first_pick: str, second_pick: str, third_pick: str):
    if not poll_running:
        response = "There is no poll active, sorry!"
    elif ctx.author.name in users_who_voted:
        response = f"You have already voted in this poll, @{ctx.author.name}."
    else:
        max_poll_id = len(current_poll_dict) + 1
        if (first_pick == second_pick or first_pick == third_pick or
                second_pick == third_pick):
            response = 'Please do not vote for the same movie multiple times.'
        elif (not 0 < int(first_pick) < max_poll_id or
              not 0 < int(second_pick) < max_poll_id or
              not 0 < int(third_pick) < max_poll_id):
            response = 'Please make sure all votes match a number on the poll.'
        else:
            try:
                response = f'Thank you for the vote @{ctx.author.name}.'

                print(ctx.author.name)
                users_who_voted.append(ctx.author.name)
                print(users_who_voted)

                first_pick_current_votes = int(
                    current_poll_dict[first_pick]['votes'])
                second_pick_current_votes = int(
                    current_poll_dict[second_pick]['votes'])
                third_pick_current_votes = int(
                    current_poll_dict[third_pick]['votes'])

                current_poll_dict[first_pick]['votes'] = first_pick_current_votes + 3

                current_poll_dict[second_pick]['votes'] = second_pick_current_votes + 2

                current_poll_dict[third_pick]['votes'] = third_pick_current_votes + 1
            except:
                response = 'Please vote for 3 movies with correct format ' + \
                 '(3 numbers [first_pick] [second_pick] [third_pick])'

    await ctx.send(response)
    print(current_poll_dict)


@bot.command(name='add', help='Add movie to the watch list. IMDB link or title accepted. Title must be in quotes.')
async def add(ctx, movie: str):
    if "imdb.com" in movie:
        imdb_id = movie.split("title/")[1].split("/")[0]
        if check_movie_id_in_list(imdb_id, viewed=False) is None:
            if add_movie_id(imdb_id, ctx.author.name):
                response = f"{movie} was added to the list."
            else:
                response = f"{movie} could not be added, double check the URL."
        else:
            response = f"{movie} is already in the list."
    else:
        # add by title
        if check_movie_title_in_list(movie, viewed=False) is None:
            found_link = search_movie_title(movie)
            if found_link:
                response = "Is this what you want to add?\n" + found_link
                message = await ctx.send(response)
                message_id = message.id
                emojis = ['\U00002705', '\U0000274c']
                for emoji in emojis:
                    await message.add_reaction(emoji)
                await asyncio.sleep(20)
                # Count reactions
                message = await ctx.fetch_message(message_id)
                reactions = {}
                for reaction in message.reactions:
                    reactions[reaction.emoji] = reaction.count
                print(reactions)
                if reactions['\U00002705'] > reactions['\U0000274c']:
                    # Add movie as it was accepted by user
                    if add_movie_title(movie, ctx.author.name):
                        response = f"{movie} was added to the list."
                    else:
                        response = "Movie could not be added. Please try again."
                else:
                    response = "Movie will not be added. Try another movie or try adding an IMDB link."
            else:
                response = f"{movie} could not be added. Double check the title or try adding an IMDB link."
        else:
            response = f"{movie} is already in the list."
    await ctx.send(response)


@bot.command(name='bulkadd', help='Add group of movies. IMDB links or titles accepted. Titles must be in quotes.')
async def bulkadd(ctx, *movies):
    response = ""
    for movie in movies:
        if "imdb.com" in movie:
            imdb_id = movie.split("title/")[1].split("/")[0]
            if check_movie_id_in_list(imdb_id, viewed=False) is None:
                if add_movie_id(imdb_id, ctx.author.name):
                    response += f"{link} was added to the list.\n"
                else:
                    response += f"{link} could not be added, double check the URL.\n"
            else:
                response += f"{link} is already in the list.\n"
        else:
            # add by title
            if check_movie_title_in_list(movie, viewed=False) is None:
                if add_movie_title(movie, ctx.author.name):
                    response += f"{movie} was added to the list.\n"
                else:
                    response += f"{movie} could not be added. Double check the title or try adding an IMDB link.\n"
            else:
                response += f"{movie} is already in the list.\n"
    await ctx.send(response)


@bot.command(name='list', help='Current unwatched movies.')
async def list(ctx):
    response = show_list(viewed=False)
    movie_list = ""
    for movie in response:
        movie_list = movie_list + \
            movie['title'] + " (" + movie['year'] + \
            "), submitted by @" + movie['submitter'] + "\n"
    await ctx.send("```" + "Unviewed Movies \n" + movie_list + "```")


@bot.command(name='viewedlist', help='Current watched movies.')
async def viewedlist(ctx):
    response = show_list(viewed=True)
    print(response)
    movie_list = ""
    for movie in response:
        movie_list = movie_list + movie['title'] + " (" + movie['year'] + \
            "), submitted by @" + \
            movie['submitter'] + ", viewed on " + \
            str(movie['viewedDate']).split(" ")[0] + "\n"
    if movie_list == "":
        await ctx.send("No movies have been viewed yet.")
    else:
        await ctx.send("```" + "Viewed Movies \n" + movie_list + "```")


@bot.command(name='setviewed', help='Put movie in viewed list. IMDB links or titles accepted. Title must be in quotes.')
async def setviewed(ctx, movie):
    if "imdb.com" in movie:
        imdb_id = movie.split("title/")[1].split("/")[0]
        if check_movie_id_in_any_list(imdb_id) is None:
            response = "Can't set movie to viewed, not in watchlist."
        elif check_movie_id_in_list(imdb_id, viewed=True) is None:
            set_viewed_by_id(imdb_id)
            response = "Movie was added to the viewed list."
        else:
            response = "Movie is already in viewed list."
    else:
        # Set viewed by title
        if check_movie_title_in_any_list(movie) is None:
            response = "Can't set movie to viewed. If it is in the unviewed list, try checking spelling with exact quotes or try IMDB link."
        elif check_movie_title_in_list(movie, viewed=True) is None:
            set_viewed_by_title(movie)
            response = "Movie was added to the viewed list."
        else:
            response = "Movie is already in viewed list."

    await ctx.send(response)


@bot.command(name='remove', help='Remove from watch list. IMDB links or titles accepted. Title must be in quotes.')
async def remove(ctx, movie: str):
    if "imdb.com" in movie:
        imdb_id = movie.split("title/")[1].split("/")[0]
        if check_movie_id_in_list(imdb_id, viewed=False):
            remove_movie_id(imdb_id)
            response = "Movie was removed from the list."
        else:
            response = "Movie could not be removed. IMDB id was not found in the list."
    else:
        # Remove by title
        if check_movie_title_in_list(movie, viewed=False):
            remove_movie_title(movie)
            response = "Movie was removed from the list."
        else:
            response = "Movie could not be removed. Double check the title in the list."
    await ctx.send(response)

bot.run(config.TOKEN)

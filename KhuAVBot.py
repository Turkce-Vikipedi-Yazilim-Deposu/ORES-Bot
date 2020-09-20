import json
import pywikibot
from pywikibot import pagegenerators
from pywikibot.data import api
from urllib import request
from urllib.error import HTTPError, URLError
import logging
import sys


def get_html(query_url):
    # Queries the website
    # We handle 500-502-503 etc server-side errors as HTTPError so the code do not crash
    try:
        response = request.urlopen(query_url)
        data = response.read()
        return data
    except HTTPError as e:
        print("EXCEPTION: get_html The server couldn't fulfill the request.")
        print("Error code: ", e.code)
        return None
    except URLError as e:
        print("EXCEPTION: get_html We failed to reach a server.")
        print("Reason: ", e.reason)
        return None
    except MemoryError:
        print('EXCEPTION: get_html Memory error')
        return None
    except:
        print('EXCEPTION: get_html Other error')
        print(sys.exc_info())
        return None


def json_printer(item, json_scores, page):
    # Just printing stuff
    message = ""
    message += str(item)
    message += "\t"
    if json_scores[str(item)]["damaging"]["prediction"] == False:
        message += "No       "
    else:
        message += "DAMAGING!"
    message += "\t"
    message += str(json_scores[str(item)]["damaging"]["probability"]["true"])[0:6]
    message += "\t"
    if json_scores[str(item)]["goodfaith"]["prediction"] == True:
        message += "No       "
    else:
        message += "BADFAITH!"
    message += "\t"
    message += str(json_scores[str(item)]["goodfaith"]["probability"]["false"])[0:6]
    message += "\t"
    message += page.latest_revision.user
    message += "\t"
    try:
        if trusted_users_list[page.latest_revision.user]:
            message += "Whitelist"
    except KeyError:
        message += "........."
    message += "\t"
    message += page.title()
    print(message)
    # logging.info(message)


def get_trusted_users():
    users_gen = api.ListGenerator(listaction="allusers", site=pywikibot.Site(), aurights='autoreview|autopatrol|bot')
    userlist = {}
    for user in users_gen:
        userlist[user["name"]] = user["userid"]
    return userlist


def is_damaging(json_scores):
    damaging = False  # This is a good edit
    for revision in json_scores:
        damaging_json = json_scores[revision]["damaging"]
        if damaging_json["prediction"] == True:
            if damaging_json["probability"]["true"] > damaging_treshhold:
                damaging = True
        return damaging


def is_badfaith(json_scores):
    badfaith = False  # This is a good edit
    for revision in json_scores:
        badfaith_json = json_scores[revision]["damaging"]
        if badfaith_json["prediction"] == True:
            if badfaith_json["probability"]["false"] > badfaith_treshhold:
                badfaith = False
        return badfaith


def reverter(page):
    history = list(page.revisions(total=2))
    userlast = history[1]["user"]
    userprev = history[0]["user"]
    comment = "Bot: ORES Test - [[Kullanıcı:{0}|{0}]] tarafından yapılan değişiklikler geri alınarak, [[Kullanıcı:" \
              "{1}|{1}]] tarafından değiştirilmiş önceki sürüm geri getirildi.".format(userlast, userprev)
    print(comment)

    old = page.text
    new = page.getOldVersion(history[1].revid)
    pywikibot.showDiff(old, new)
    # page.save(comment) # Currently not saving anything!


def main():
    print("Revid\tDamaging?\t%Dmg\tBadfaith?\t%BF\tUser\tUsertype\tPage")
    for page in generator:
        try:
            if page._rcinfo['namespace'] == 0:
                ores_scores = get_html(ores_query+str(page.latest_revision_id))
                json_scores = json.loads(ores_scores)
                damaging = is_damaging(json_scores)
                badfaith = is_badfaith(json_scores)
                json_printer(str(page.latest_revision_id), json_scores, page)
                if damaging and badfaith:
                    reverter(page)

        except pywikibot.exceptions.NoPage:
            print("NOPAGE")
            pass

        except:
            # Too broad exception
            print("Error...", end="\t")
            print(sys.exc_info())
            pass


if __name__ == "__main__":
    ores_query = "https://ores.wikimedia.org/scores/trwiki?models=damaging|goodfaith&revids="
    damaging_treshhold = 0.7
    badfaith_treshhold = 0.7

    project = pywikibot.Site('tr', 'wikipedia')
    site = pywikibot.Site()
    generator = pagegenerators.LiveRCPageGenerator(site, total=None)
    trusted_users_list = get_trusted_users()

    # Run Forrest, RUN!
    main()

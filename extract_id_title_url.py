#!/usr/bin/env python2.7
# encoding: utf-8
'''
extract_id_title.py

Created by Hallvord R. M. Steen on 2014-10-25.
Modified by Karl
Mozilla Public License, version 2.0
see LICENSE

Dumps data from webcompat.com bug tracker
by default creates one CSV file (webcompatdata.csv)
and one JSON file (webcompatdata-bzlike.json)
the JSON file uses many of the field names Bugzilla uses in its export,
so the output from this script can be used where Bugzilla data is expected
'''

import csv
import json
import re
import socket
import sys
from urllib.request import Request
from urllib.request import urlopen


# Config
URL_REPO = "https://api.github.com/repos/webcompat/web-bugs"
VERBOSE = True
# Seconds. Loading searches can be slow
socket.setdefaulttimeout(240)


def get_remote_file(url, req_json=False):
    print('Getting ' + url)
    req = Request(url)
    req.add_header('User-agent', 'AreWeCompatibleYetBot')
    if req_json:
        req.add_header('Accept', 'application/vnd.github.v3+json')
    bzresponse = urlopen(req, timeout=240)
    return {"headers": bzresponse.info(),
            "data": json.loads(bzresponse.read().decode('utf8'))}


def extract_url(issue_body):
    '''Extract the URL for an issue from WebCompat.

    URL in webcompat.com bugs follow this pattern:
    **URL**: https://example.com/foobar
    '''
    url_pattern = re.compile('\*\*URL\*\*\: (.*)\n')
    url_match = re.search(url_pattern, issue_body)
    if url_match:
        url = url_match.group(1).strip()
        if not url.startswith(('http://', 'https://')):
            url = "http://%s" % url
    else:
        url = ""
    return url


def extract_data(json_data, results_csv, results_bzlike):
    resolution_labels = ["duplicate", "invalid", "wontfix", "fixed",
                         "worksforme"]
    whiteboard_labels = ["needsinfo", "contactready", "sitewait",
                         "needscontact", "needsdiagnosis"]
    for issue in json_data["data"]:
        # Extracting data
        body = issue["body"]
        url = extract_url(body)
        bug_id = issue["number"]
        link = 'https://webcompat.com/issues/%s' % bug_id
        issue_title = issue["title"].strip()
        if VERBOSE:
            print('Issue %s: %s' % (bug_id, issue_title))
        creation_time = issue['created_at']
        last_change_time = issue['updated_at']
        issue_state = issue['state']
        cf_last_resolved = issue['closed_at']
        if issue_state == 'open':
            status = 'OPEN'
        else:
            status = 'RESOLVED'
        # Extracting the labels
        labels_list = [label['name'] for label in issue['labels']]
        # areWEcompatibleyet is only about mozilla bugs
        if any([('firefox' or 'mozilla') in label for label in labels_list]):
            # Defining the OS
            if any(['mobile' in label for label in labels_list]):
                op_sys = 'Gonk (Firefox OS)'
            elif any(['android' in label for label in labels_list]):
                op_sys = 'Android'
            else:
                op_sys = ''
            # Did the bug had a resolution?
            resolution = ''
            resolution_set = set(labels_list).intersection(resolution_labels)
            if resolution_set:
                resolution = resolution_set.pop().upper()
            # Gathering Whiteboard keys
            whiteboard = ''.join(['[%s] ' % label for label in labels_list
                                  if label in whiteboard_labels])
            # creating CSV file
            if issue_title:
                results_csv.append("%i\t%s\t%s\t%s" % (
                    bug_id, issue_title, url, link))
            # Creating dictionary
            bzlike = {"id": bug_id,
                      "summary": issue_title,
                      "url": url,
                      "whiteboard": whiteboard,
                      "op_sys": op_sys,
                      "creation_time": creation_time,
                      "last_change_time": last_change_time,
                      "status": status,
                      "cf_last_resolved": cf_last_resolved,
                      "resolution": resolution,
                      "body": body
                      }
            results_bzlike.append(bzlike)


def extract_next_link(link_hdr):
    '''Given a HTTP Link header, extract the "next" link.

    Link header has the pattern:
    '<https://example.com/foobar?page=2>; rel="next",
     <https://example.com/foobar?page=100>; rel="last"'
    We need:
    https://example.com/foobar?page=2
    When no more "next", we return an empty string.
    '''
    next_link = ''
    links = link_hdr.split(',')
    for link in links:
        link_only, rel = link.split(';')
        if 'next' in rel:
            next_link = link_only.strip(' <>')
            break
    return next_link


def get_webcompat_data(url_repo=URL_REPO):
    '''Extract Issues data from github repo.

    Start with the first page and follow hypermedia links to explore the rest.
    '''
    next_link = '%s/issues?per_page=100&page=1&filter=all&state=all' % (url_repo)
    results = []
    bzresults = []

    while next_link:
        response_data = get_remote_file(next_link, True)
        extract_data(response_data, results, bzresults)
        next_link = extract_next_link(response_data["headers"]["link"])
    return results, {"bugs": bzresults}


def main():
    results, bzresults = get_webcompat_data(URL_REPO)
    # webcompatdata.csv
    with open('webcompatdata.csv', 'w') as f:
        f.write("\n".join(results))
    print("Wrote {} items to webcompatdata.csv ".format(len(results)))
    # webcompatdata-bzlike.json
    with open('webcompatdata-bzlike.json', 'w') as f:
        f.write(json.dumps(bzresults, indent=4))
    print("Wrote {} items to webcompatdata-bzlike.json".format(
        len(bzresults['bugs'])))


if __name__ == "__main__":
    sys.exit(main())

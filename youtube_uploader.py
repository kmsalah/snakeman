import httplib
import httplib2
import os
import random
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


CLIENT_SECRETS_FILE = "client_secrets.json"


# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = "'"

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]




class Youtube:
  def __init__(self):
  	print("yeet")
 
  def upload(self):
    #override sys.argv
    argparser.add_argument("--file", required=True, help="Video file to upload")
    argparser.add_argument("--title", help="Video title", default="Test Title")
    argparser.add_argument("--description", help="Video description",
      default="Test Description")
    argparser.add_argument("--category", default="22",
      help="Numeric video category. " +
        "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", help="Video keywords, comma separated",
      default="")
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES,
    default=VALID_PRIVACY_STATUSES[0], help="Video privacy status.")

    #override args
    sys.argv = ['uploader.py', '--file', './sample_video.mp4', '--title', "Summer vacation in California",
                       '--description', "Had fun surfing in Santa Cruz",
                       '--keywords', "surfing,Santa Cruz",
                       '--category' ,"22",
                       '--privacyStatus', "private"]
    args = argparser.parse_args()



    youtube = self.get_authenticated_service(args)
    try:
      self.initialize_upload(youtube, args)
    except HttpError, e:
      print(e)
    return "werxw"


  def initialize_upload(self, youtube, options):
    tags = None
    if options.keywords:
      tags = options.keywords.split(",")
  
    body=dict(
      snippet=dict(
        title=options.title,
        description=options.description,
        tags=tags,
        categoryId=options.category
    ),
      status=dict(
        privacyStatus=options.privacyStatus
      )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
      part=",".join(body.keys()),
      body=body,
      # The chunksize parameter specifies the size of each chunk of data, in
      # bytes, that will be uploaded at a time. Set a higher value for
      # reliable connections as fewer chunks lead to faster uploads. Set a lower
      # value for better recovery on less reliable connections.
      #
      # Setting "chunksize" equal to -1 in the code below means that the entire
      # file will be uploaded in a single HTTP request. (If the upload fails,
      # it will still be retried where it left off.) This is usually a best
      # practice, but if you're using Python older than 2.6 or if you're
      # running on App Engine, you should set the chunksize to something like
      # 1024 * 1024 (1 megabyte).
      media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )
    self.resumable_upload(insert_request)
  
  def resumable_upload(self,insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
      print("yeet")
      try:
        print "Uploading file..."
        status, response = insert_request.next_chunk()
        if 'id' in response:
          print "Video id '%s' was successfully uploaded." % response['id']
        else:
          exit("The upload failed with an unexpected response: %s" % response)
      except HttpError, e:
        if e.resp.status in RETRIABLE_STATUS_CODES:
          error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                         e.content)
        else:
          raise
      except RETRIABLE_EXCEPTIONS, e:
        error = "A retriable error occurred: %s" % e

      if error is not None:
        print error
        retry += 1
        if retry > MAX_RETRIES:
          exit("No longer attempting to retry.")

        max_sleep = 2 ** retry
        sleep_seconds = random.random() * max_sleep
        print "Sleeping %f seconds and then retrying..." % sleep_seconds
        time.sleep(sleep_seconds)
  def get_authenticated_service(self, args):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
      scope=YOUTUBE_UPLOAD_SCOPE,
      message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()
    if credentials is None or credentials.invalid:
      credentials = run_flow(flow, storage, args)
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
      http=credentials.authorize(httplib2.Http()))

	
from flask import Flask
from youtube_uploader import Youtube

uploader = Flask(__name__)
youtube = Youtube()


upload_funcs = {
	'youtube': youtube.upload()
}


@uploader.route('/')
def index():
  return 'root'

@uploader.route('/<path:service>/upload')
def upload(service):
	return upload_funcs[service]
  #
if __name__ == '__main__':
  uploader.run(debug=True)




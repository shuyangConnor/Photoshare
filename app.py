######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for, flash
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'fjLan4416'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	def is_authenticated(self): 
		return True
	

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out', activeUsers = getActiveUsers(), popularTags = getPopularTags(),public_photos=getAllPhotos(), base64=base64)

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		gender=request.form.get('gender')
		dob=request.form.get('dob')
		hometown=request.form.get('hometown')
		fname=request.form.get('fname')
		lname=request.form.get('lname')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, gender, dob, hometown, fname, lname) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, gender, dob, hometown, fname, lname)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return render_template('register.html')

def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
    photos = cursor.fetchall()
    updated_photos = []
    for photo in photos:
        tags = getTagsForPhoto(photo[1])
        updated_photo = photo + (tags,)
        updated_photos.append(updated_photo)
    return updated_photos

   


def getAllPhotos():
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures")
    photos = cursor.fetchall()

    updated_photos = []
    for photo in photos:
        cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id = %s", (photo[1],))
        num_likes = cursor.fetchone()[0]
        cursor.execute("SELECT email FROM Users INNER JOIN Likes ON Users.user_id = Likes.user_id WHERE Likes.picture_id = %s", (photo[1],))
        likes = cursor.fetchall()
        tags = getTagsForPhoto(photo[1])
        comments = getPhotoComments(photo[1])
        updated_photo = photo + (num_likes,) + (likes,) + (tags,) + (comments,)
        updated_photos.append(updated_photo)

    return updated_photos
  
def getContribution():
  result ={}
  cursor=conn.cursor()
  cursor.execute('''SELECT u.email, COUNT(c.comment_id)
FROM Users u
LEFT JOIN Comments c ON u.user_id = c.user_id
GROUP BY u.user_id;
''')
  commentCount = cursor.fetchall()
  cursor.execute('''SELECT u.email, COUNT(p.picture_id)
FROM Users u
LEFT JOIN Pictures p ON u.user_id = p.user_id
GROUP BY u.user_id;
''')
  photoCount = cursor.fetchall()
  # print(photoCount)
  for ccount in commentCount:
    if ccount[0] in result:
      result[ccount[0]]+=ccount[1]
    else:
      result[ccount[0]]=ccount[1]
  for pcount in photoCount:
    if pcount[0] in result:
      result[pcount[0]]+=pcount[1]
    else:
      result[pcount[0]]=pcount[1]
  result = list(sorted(result.items(), key=lambda x: x[1], reverse=True))
  return result

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def doesUserHaveAlbum(uid, aname):
	cursor = conn.cursor()
	if cursor.execute("SELECT name FROM Albums WHERE user_id = '{0}' AND name = '{1}'".format(uid, aname)):
		return True
	else:
		return False

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()
#end login code

def getAlbumId(name):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM Albums WHERE name = '{0}'".format(name))
	return cursor.fetchall()

def	getActiveUsers():
	cursor = conn.cursor()
	cursor.execute("SELECT U.email FROM Users U JOIN Pictures P ON U.user_id = P.user_id GROUP BY U.user_id ORDER BY COUNT(*) DESC LIMIT 10")
	return cursor.fetchall()

def getUserFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT U.email FROM Users U WHERE U.user_id IN ( SELECT F.UID2 FROM Friendship F WHERE F.UID1 = '{0}')".format(uid))
	return cursor.fetchall()

def getRecommendFriends(friends):
  count = {}
  for email in friends:
    # print(email)
    cursor = conn.cursor()
    cursor.execute("SELECT U1.email FROM Users U1 WHERE EXISTS (SELECT * FROM Friendship F WHERE U1.user_id = F.UID2 AND F.UID1 = (SELECT U2.user_id FROM Users U2 WHERE U2.email = '{0}'))".format(email[0]))
    tmp = cursor.fetchall()
    for friend in tmp:
      if friend[0] in count:
        count[friend[0]]+=1
      else:
        count[friend[0]]=1
  result = sorted(count.items(), key=lambda x: x[1], reverse=True)
  print(result)
  return result

def addFriend(uid, femail):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Friendship (UID1, UID2) SELECT {0}, user_id FROM Users WHERE email = '{1}'".format(uid,femail))
	conn.commit()
 
def deletePhoto(pid):
  cursor = conn.cursor()
  cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pid))
  conn.commit()
  
def deleteAlbum(aname):
  cursor = conn.cursor()
  cursor.execute("DELETE FROM Albums WHERE name = '{0}'".format(aname))
  conn.commit()
  
def getTagID(tag_name):
    cursor = conn.cursor()
    cursor.execute("SELECT tag_id FROM Tags WHERE name='{0}'".format(tag_name))
    tag = cursor.fetchone()
    if tag:
      return tag[0]
    else:
      cursor.execute("INSERT INTO Tags (name) VALUES ('{0}')".format(tag_name))
      conn.commit()
      return cursor.lastrowid

def addTagForPhoto(tag):
  cursor = conn.cursor()
  tid = getTagID(tag)
  cursor.execute("SELECT MAX(picture_id) FROM Pictures;")
  pid = cursor.fetchone()[0]
  cursor.execute("INSERT INTO Tagged (picture_id, tag_id) VALUES ('{0}', '{1}')".format(pid, tid))
  conn.commit()

def getTagsForPhoto(pid):
  cursor = conn.cursor()
  cursor.execute("SELECT Tags.name FROM Tagged INNER JOIN Tags ON Tagged.tag_id = Tags.tag_id WHERE Tagged.picture_id = {0}".format(pid))
  return cursor.fetchall()

def getAllPhotosWithTag(name):
    cursor = conn.cursor()
    cursor.execute("SELECT p.imgdata, p.picture_id, p.caption FROM Pictures p JOIN Tagged t ON p.picture_id = t.picture_id JOIN Tags tg ON t.tag_id = tg.tag_id WHERE tg.name = '{0}'".format(name))
    photos = cursor.fetchall()
    return photos

def getYourPhotosWithTag(name, uid):
  cursor = conn.cursor()
  cursor.execute("SELECT p.imgdata, p.picture_id, p.caption FROM Pictures p JOIN Tagged t ON p.picture_id = t.picture_id JOIN Tags tg ON t.tag_id = tg.tag_id WHERE tg.name = '{0}' AND p.user_id = '{1}'".format(name, uid))
  photos = cursor.fetchall()
  return photos

def getPopularTags():
  cursor = conn.cursor()
  cursor.execute('''SELECT t.name
FROM Tags t
JOIN Tagged tg ON t.tag_id = tg.tag_id
GROUP BY t.tag_id
ORDER BY COUNT(tg.picture_id) DESC
LIMIT 3''')
  tags = cursor.fetchall()
  return tags

def getPhotoComments(pid):
  cursor = conn.cursor()
  cursor.execute("SELECT text FROM Comments WHERE picture_id = {0}".format(pid))
  comments = cursor.fetchall()
  return comments
  
def getThreeFrequentTags(uid):
  cursor = conn.cursor()
  cursor.execute("SELECT t.name AS tag_count FROM Tags t JOIN Tagged td ON t.tag_id = td.tag_id JOIN Pictures p ON td.picture_id = p.picture_id WHERE p.user_id = {0} GROUP BY t.name ORDER BY tag_count DESC LIMIT 3".format(uid))  
  result= cursor.fetchall()
  return result

def getRecommendPhotos(tags):
  uid= getUserIdFromEmail(flask_login.current_user.id)
  cursor = conn.cursor()
  # print("WUHWUHWUUWHU%s", (tags[1][0]))
  cursor.execute('''SELECT p.imgdata,p.picture_id, p.caption, COUNT(t.tag_id) as tag_count, p.user_id
FROM Pictures p
LEFT JOIN Tagged tg ON p.picture_id = tg.picture_id
LEFT JOIN Tags t ON tg.tag_id = t.tag_id AND t.name IN ('{0}', '{1}', '{2}')
GROUP BY p.picture_id
ORDER BY tag_count DESC;
'''.format(tags[0][0], tags[1][0], tags[2][0]))
  tmp = cursor.fetchall()
  result = []
  for photo in tmp:
    tags = getTagsForPhoto(photo[1])
    comments = getPhotoComments(photo[1])
    updated_photo = photo + (tags,) + (comments,)
    if photo[4] != uid:
      result.append(updated_photo)
  return result

def getPhotosWithAllTags(names):
    cursor = conn.cursor()
    cursor.execute("SELECT picture_id FROM Pictures")
    picture_ids = [row[0] for row in cursor.fetchall()]

    filtered_picture_ids = []
    for picture_id in picture_ids:
        cursor.execute("SELECT COUNT(*) FROM Tagged WHERE picture_id = %s AND tag_id IN (SELECT tag_id FROM Tags WHERE name IN %s)", (picture_id, tuple(names)))
        count = cursor.fetchone()[0]
        if count>=len(names):
          
          filtered_picture_ids.append(picture_id)
        # if count == count2 and count <= len(names):
    if filtered_picture_ids:
        cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id IN ({})".format(', '.join(['%s']*len(filtered_picture_ids))), filtered_picture_ids)
        result = cursor.fetchall()
        updated=[]
        for img in result:
          tags = getTagsForPhoto(img[1])
          updated_photo = img+(tags,)
          updated.append(updated_photo)
        return updated
    else:
        return []

@app.route('/profile', methods=['GET'])
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=getUsersPhotos(uid), base64=base64)

@app.route('/profile', methods=['POST'])
@flask_login.login_required
def delete_photo():
  uid = getUserIdFromEmail(flask_login.current_user.id)
  photo_id = request.form.get('photo_id')
  deletePhoto(photo_id)
  return render_template('hello.html', name=flask_login.current_user.id, message="Photo deleted!", photos=getUsersPhotos(uid), base64=base64)
  

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	albums = getUsersAlbums(uid)
	if request.method == 'POST':
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album = request.form.get('album')
		tags = request.form.get('tags').split(" ")
		if (doesUserHaveAlbum(uid, album) == False):
			return '''
			   <li>The album you entered does not exist. Please try again.</li>
		   <a href='/upload'>Go back</a>
			   '''
		aid=getAlbumId(album)
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, aid))
		conn.commit()
		for tag in tags:
			addTagForPhoto(tag)
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html', albums = albums)
		
#end photo uploading code

@app.route('/createAlbum', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	albums = getUsersAlbums(uid)
	if request.method == 'POST':
		name = request.form.get('name')
		if (doesUserHaveAlbum(uid, name) == True):
			return '''
			   <li>The album you entered already exists. Please try again.</li>
		   <a href='/createAlbum'>Go back</a>
			   '''
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (user_id, name) VALUES (%s, %s)''', (uid, name))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album created!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('createAlbum.html', albums = albums)

@app.route('/deleteAlbum', methods=['POST'])
@flask_login.login_required
def delete_album():
  uid = getUserIdFromEmail(flask_login.current_user.id)
  album_name = request.form.get('album_name')
  deleteAlbum(album_name)
  albums = getUsersAlbums(uid)
  return render_template('createAlbum.html', albums = albums)

@app.route('/friend', methods=['GET', 'POST'])
@flask_login.login_required
def friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		friend_email = request.form.get('friend_email')
		try:
			addFriend(uid, friend_email)
		except:
			flash("Invalid friend.")
		return render_template('friend.html', friends = getUserFriends(uid))
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		friends = getUserFriends(uid)
		recommend_friends=getRecommendFriends(friends)
		return render_template('friend.html', friends = friends, recommend_friends=recommend_friends)

#default page
@app.route("/", methods=['GET'])
def hello():
  return render_template('hello.html', activeUsers = getContribution(), popularTags = getPopularTags(), message='Welecome to Photoshare', public_photos=getAllPhotos(), base64=base64)

@app.route("/", methods=['POST'])
@flask_login.login_required
def like_photo():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	photo_id=request.form.get('photo_id')
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, photo_id))
	liked = cursor.fetchall()
	if not liked:
		cursor.execute("INSERT INTO Likes(user_id, picture_id) VALUES ('{0}', '{1}')".format(uid, photo_id))
		conn.commit()
	else:
		flash("You have already liked this picture.")
	return render_template('hello.html', activeUsers = getActiveUsers(),message='Welecome to Photoshare', public_photos=getAllPhotos(), base64=base64)

@app.route('/viewAllPhotosWithTag')
def viewAllPhotosWithTag():
		name = request.args.get('name')
		allPhotos = getAllPhotosWithTag(name)
		return render_template('photosWithTag.html', photos=allPhotos, tag=name, base64=base64)

@app.route('/viewYourPhotosWithTag')
def viewYourPhotosWithTag():
		name = request.args.get('name')
		uid = getUserIdFromEmail(flask_login.current_user.id)
		allPhotos = getYourPhotosWithTag(name, uid)
		return render_template('photosWithTag.html', photos=allPhotos, tag=name, yours = "True", base64=base64)

@app.route('/searchTags', methods=['POST'])
def searchTags():
		names = request.form.get('name').split(" ")
		allPhotos=getPhotosWithAllTags(names)
		# print(allPhotos)
		return render_template('photosWithTag.html', photos=allPhotos, tags = names, base64=base64)

@app.route('/makeComment', methods=['POST'])
def makeComment():
		comment = request.form.get('comment')
		pid = request.form.get('photo_id')
		if flask_login.current_user.is_authenticated:
			uid = getUserIdFromEmail(flask_login.current_user.id)
		else:
			uid = None
		try:
			cursor = conn.cursor()
			cursor.execute('''INSERT INTO Comments (text, user_id, picture_id) VALUES (%s, %s, %s)''', (comment, uid, pid))
			conn.commit()
		except:
			flash("You can't comment on your own photo!")
		return render_template('hello.html', activeUsers = getActiveUsers(), popularTags = getPopularTags(), message='Welecome to Photoshare', public_photos=getAllPhotos(), base64=base64)

@app.route('/searchComment', methods=['POST'])
def searchComment():
		comment = request.form.get('comment')
		cursor=conn.cursor()
		cursor.execute("SELECT Users.email, COUNT(*) as count FROM Users JOIN Comments ON Users.user_id = Comments.user_id WHERE Comments.text LIKE '{0}' GROUP BY Users.user_id ORDER BY count DESC".format(comment))
		users = cursor.fetchall()
		return render_template('searchComment.html', users=users, comment = comment)

@app.route('/alsoLike', methods=['GET'])
@flask_login.login_required
def alsoLike():
		uid = getUserIdFromEmail(flask_login.current_user.id)
		three = getThreeFrequentTags(uid)
		recommend_photos=getRecommendPhotos(three)
		return render_template('hello.html', tags=three,activeUsers = getActiveUsers(), popularTags = getPopularTags(), message='Welecome to Photoshare', recommend_photos=recommend_photos, base64=base64)

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
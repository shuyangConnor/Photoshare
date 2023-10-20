DROP DATABASE IF EXISTS photoshare;
CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;

CREATE TABLE Users (
    user_id int4 not null AUTO_INCREMENT,
    gender varchar(6),
    email varchar(255) UNIQUE,
    password varchar(255),
    dob date not null,
    hometown varchar(40),
    fname varchar(40) not null,
    lname varchar(40) not null,
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Albums(
  album_id int4 not null AUTO_INCREMENT,
  name varchar(40) UNIQUE NOT NULL,
  date_of_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
  user_id int4 NOT NULL,
  PRIMARY KEY (album_id),
  FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Pictures(
picture_id int4 AUTO_INCREMENT,
user_id int4,
caption varchar(200),
imgdata LONGBLOB,
album_id int4 NOT NULL,
PRIMARY KEY(picture_id),
FOREIGN KEY(user_id) REFERENCES Users(user_id),
FOREIGN KEY(album_id) REFERENCES Albums(album_id) ON DELETE CASCADE
);


CREATE TABLE Comments(
comment_id int4 NOT NULL AUTO_INCREMENT,
text TEXT NOT NULL,
date DATETIME DEFAULT CURRENT_TIMESTAMP,
user_id int4,
picture_id int4 NOT NULL,
PRIMARY KEY(comment_id),
FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
FOREIGN KEY(picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE
);

CREATE TABLE Likes(
	user_id INT NOT NULL,
	picture_id INT NOT NULL,
	PRIMARY KEY (picture_id, user_id),
	FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE, FOREIGN KEY (picture_id) REFERENCES Pictures (picture_id) ON DELETE
	CASCADE 
);

CREATE TABLE Tags(
  tag_id int4 NOT NULL AUTO_INCREMENT,
  name varchar(100),
  PRIMARY KEY (tag_id)
);

CREATE TABLE Tagged(
  picture_id int,
  tag_id int,
  PRIMARY KEY (picture_id, tag_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES Tags (tag_id) ON DELETE CASCADE
);

CREATE TABLE Friendship (
	UID1 INT NOT NULL,
	UID2 INT NOT NULL,
	CHECK (UID1 <> UID2),
	PRIMARY KEY(UID1, UID2),
	FOREIGN KEY (UID1) REFERENCES Users (user_id) ON DELETE CASCADE, FOREIGN KEY (UID2) REFERENCES Users (user_id) ON DELETE CASCADE
);

CREATE TRIGGER comment_constraint_trigger AFTER INSERT ON Comments FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT * FROM Comments C, Pictures P
        WHERE C.picture_id = P.picture_id AND P.user_id = NEW.user_id
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Comment constraint violation';
    END IF;
END;

INSERT INTO Users (email, password, gender, dob, hometown, fname, lname) VALUES ('test@bu.edu', 'test', 'male',  '2022-09-01','Boston', 'Shuyang', 'Connor');
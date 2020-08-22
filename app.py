#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://postgres:admin@localhost:5432/fyyur"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = 'Venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120), nullable=True)
  website = db.Column(db.String(120), nullable=True)
  show = db.relationship("Show", backref="venue_show", lazy=True)

  def __repr__(self):
    return f"<Venue {self.id}, {self.name}, {self.city}, {self.state}>"

class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website = db.Column(db.String(120), nullable=True)
  show = db.relationship("Show", backref="artist_show", lazy=True)

class Show(db.Model):
  __tablename__ = "Show"

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
  start_date = db.Column(db.DateTime, nullable=False)

  def __repr__(self):
    return f"<Show {self.artist_id}, {self.venue_id}, {self.start_date}>"

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
    format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
    format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  for venue in Venue.query.distinct(Venue.city).distinct(Venue.state):
    data.append({
      "city": venue.city,
      "state": venue.state,
      "venues": []
    })
  for area in data:
    venues = Venue.query.filter(Venue.city == area["city"] and Venue.state == area["state"]).all()
    for venue in venues:
      area["venues"].append({
        "id": venue.id,
        "name": venue.name
      })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
  response={
    "count": len(venues),
    "data": []
  }
  for venue in venues:
    response["data"].append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": 0
    })
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = Venue.query.get(venue_id)
  venue_data = {
    "id": data.id,
    "name": data.name,
    "genres": [data.genres],
    "city": data.city,
    "state": data.state,
    "address": data.address,
    "phone": data.phone,
    "seeking_venue": False,
    "image_link": data.image_link
  }

  past_shows = []
  upcoming_shows = []
  shows = Show.query.filter(Show.venue_id == venue_id).join(Artist, Artist.id == Show.artist_id).add_columns(Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link")).all()
  for item in shows:
    show = item.Show
    showData = {
      "artist_id": show.artist_id,
      "start_date": (show.start_date).strftime("%m/%d/%Y, %H:%M:%S"),
      "artist_name": item.artist_name,
      "artist_image_link": item.artist_image_link,
    }
    if datetime.datetime.now() >= show.start_date: past_shows.append(showData)
    else: upcoming_shows.append(showData)
  
  venue_data["past_shows_count"] = len(past_shows)
  venue_data["upcoming_shows_count"] = len(upcoming_shows)
  venue_data["past_shows"] = past_shows
  venue_data["upcoming_shows"] = upcoming_shows

  return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  
  error = False
  try:
    venue = Venue(
      name=request.form["name"], city=request.form["city"], 
      state=request.form["state"], address=request.form["address"], phone=request.form["phone"], 
      genres=request.form["genres"], image_link=request.form["image_link"],
      facebook_link=request.form["facebook_link"], website=request.form["website"]
    )
    db.session.add(venue)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()

  if error:
    flash('Something went wrong while adding Venue ' + request.form['name'])
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    Venue.query.filter(Venue.id == venue_id).delete()
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    
  if error:
    abort (400)
  else:
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  venues = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()
  response={
    "count": len(venues),
    "data": []
  }
  for venue in venues:
    response["data"].append({
      "id": venue.id,
      "name": venue.name
    })
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = Artist.query.get(artist_id)
  artist_data={
    "id": data.id,
    "name": data.name,
    "genres": [data.genres],
    "city": data.city,
    "state": data.state,
    "phone": data.phone,
    "seeking_venue": False,
    "image_link": data.image_link
  }

  past_shows = []
  upcoming_shows = []
  shows = Show.query.filter(Show.artist_id == artist_id).join(Venue, Venue.id == Show.venue_id).add_columns(Venue.name.label("venue_name"), Venue.image_link.label("venue_image_link")).all()
  for item in shows:
    show = item.Show
    showData = {
      "venue_id": show.venue_id,
      "start_date": (show.start_date).strftime("%m/%d/%Y, %H:%M:%S"),
      "venue_name": item.venue_name,
      "venue_image_link": item.venue_image_link,
    }
    if datetime.datetime.now() >= show.start_date: past_shows.append(showData)
    else: upcoming_shows.append(showData)
  
  artist_data["past_shows_count"] = len(past_shows)
  artist_data["upcoming_shows_count"] = len(upcoming_shows)
  artist_data["past_shows"] = past_shows
  artist_data["upcoming_shows"] = upcoming_shows
  
  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  form = request.form
  artist.name = form.get('name')
  artist.city = form.get('city')
  artist.state = form.get('state')
  artist.phone = form.get('phone')
  artist.genres = form.get('genres')
  artist.image_link = form.get('image_link', '')
  artist.facebook_link = form.get('facebook_link', '')
  artist.website = form.get('website', '')
  
  error = False
  try:
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    
  if error:
    abort (400)
  else:
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  form = request.form
  venue.name = form.get('name')
  venue.city = form.get('city')
  venue.state = form.get('state')
  venue.address = form.get('address')
  venue.phone = form.get('phone')
  venue.genres = form.get('genres')
  venue.image_link = form.get('image_link', '')
  venue.facebook_link = form.get('facebook_link', '')
  venue.website = form.get('website', '')
  
  error = False
  try:
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    
  if error:
    abort (400)
  else:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    artist = Artist(
      name=request.form["name"], city=request.form["city"], 
      state=request.form["state"], phone=request.form["phone"], 
      genres=request.form["genres"], image_link=request.form["image_link"],
      facebook_link=request.form["facebook_link"], website=request.form["website"]
    )
    db.session.add(artist)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()

  if error:
    flash('Something went wrong while adding Artist ' + request.form['name'])
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  joinedData = Show.query.join(Venue, Venue.id == Show.venue_id).add_columns(Venue.name.label("venue_name")).join(Artist, Artist.id == Show.artist_id).add_columns(Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link")).all()
  data = []
  for item in joinedData:
    show = item.Show
    data.append({
      "venue_id": show.venue_id,
      "artist_id": show.artist_id,
      "start_date": (show.start_date).strftime("%m/%d/%Y, %H:%M:%S"),
      "venue_name": item.venue_name,
      "artist_name": item.artist_name,
      "artist_image_link": item.artist_image_link
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    show = Show(
      artist_id=request.form["artist_id"], venue_id=request.form["venue_id"], 
      start_date=request.form["start_date"]
    )
    db.session.add(show)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()

  if error:
    flash('Show was not added. Something went wrong!')
  else:
    flash('Show was added successfully!')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
  return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
  return render_template('errors/500.html'), 500


if not app.debug:
  file_handler = FileHandler('error.log')
  file_handler.setFormatter(
    Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
  )
  app.logger.setLevel(logging.INFO)
  file_handler.setLevel(logging.INFO)
  app.logger.addHandler(file_handler)
  app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
  app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

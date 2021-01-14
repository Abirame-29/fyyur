#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime, date
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
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
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'
    

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
      return f'<Artist {self.id} {self.name}>'

class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  print('format datetime : ', value, type(value))
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  print("recently listed")
  artists = Artist.query.order_by(Artist.id.desc())
  venues = Venue.query.order_by(Venue.id.desc())
  data = []
  i = 0
  j = 0
  while (i<artists.count() and j<venues.count() and len(data)<10):
    if(artists[i].id > venues[j].id):
      data.append({"id":artists[i].id, "name" : artists[i].name, "type" : "artist"})
      i += 1
    else:  
      data.append({"id":venues[j].id, "name" : venues[j].name, "type" : "venue"})
      j += 1
  while(len(data)<10 and j<venues.count()):
    data.append({"id":venues[j].id, "name" : venues[j].name, "type" : "venue"})
    j += 1
  while(len(data)<10 and i<artists.count()):
    data.append({"id":artists[i].id, "name" : artists[i].name, "type" : "artist"})
    i += 1
  return render_template('pages/home.html', data=data)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  query_place_list = Venue.query.with_entities(Venue.city, Venue.state).all()
  state_list = {}
  for place in query_place_list:
    l = str(place).split(',')
    city = l[0][2:-1]
    state = l[1][2:4]
    if state in state_list:
      state_list[state].add(city)
    else:
      state_list[state] = {city,}
  data = []
  for state, cities in state_list.items():
    for city in cities:
      venues = Venue.query.filter(Venue.city==city,Venue.state==state).all()
      dict1 = {"city" : city, "state" : state}
      venue_list = []
      for venue in venues:
        num = db.session.query(Venue).join(Show).filter(Venue.id==venue.id, Show.start_time > datetime.now()).count()
        venue_dict = {"id" : venue.id, "name" : venue.name, "num_upcoming_shows" : num}
        venue_list.append(venue_dict)
      dict1["venues"] = venue_list
      data.append(dict1)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  searchby = request.form.get('searchby','')
  search = request.form.get('search_term', '')
  if(searchby=='area'):
    if ',' in search:
      cityName = search.split(',')[0]
      stateName = search.split(',')[1].replace(' ','')
      venues = Venue.query.filter(Venue.state.ilike("%" + stateName + "%")).filter(Venue.city.ilike("%" + cityName + "%")).all()
    else:
      venues = Venue.query.filter(Venue.state.ilike("%" + search + "%")).all()
      venues += Venue.query.filter(Venue.city.ilike("%" + search + "%")).all()
  else:
    venues = Venue.query.filter(Venue.name.ilike("%" + search + "%")).all()  
  data = []
  for venue in venues:
    upcoming_shows = db.session.query(Show).join(Venue).filter(venue.id==Venue.id, Show.start_time > datetime.now()).count()                  
    data.append({
      "id" : venue.id,
      "name" : venue.name,
      "num_upcoming_shows" : upcoming_shows
    })
  response={
    "count": len(venues),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  
  past_shows = db.session.query(Show).join(Venue).filter(Venue.id==venue.id, Show.start_time < datetime.now()).all()
  past_shows_list = []
  for show in past_shows:
    artist = Artist.query.get(show.artist_id)
    dict1 = {
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    }
    past_shows_list.append(dict1)

  upcoming_shows = db.session.query(Show).join(Venue).filter(Venue.id==venue.id, Show.start_time > datetime.now()).all()
  upcoming_shows_list = []
  for show in upcoming_shows:
    artist = Artist.query.get(show.artist_id)
    dict1 = {
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    }
    upcoming_shows_list.append(dict1)
  
  data["past_shows"] = past_shows_list
  data["upcoming_shows"] = upcoming_shows_list
  data["past_shows_count"] = len(past_shows_list)
  data["upcoming_shows_count"] = len(upcoming_shows_list)
  return render_template('pages/show_venue.html', venue=data)

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
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      address = request.form['address'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      genres = request.form.getlist('genres'),
      website = request.form['website'],
      seeking_description = request.form['seeking_description']
    )
    if 'seeking_talent' not in request.form:
      venue.seeking_talent = False
    else:
      venue.seeking_talent = True
    db.session.add(venue)
    db.session.commit()
  except Exception as e:
    print(e)
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error:
    #abort(400)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return redirect(url_for('index'))


@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
  print("delete function : ", venue_id)
  error = False
  name = ''
  try:
    venue = Venue.query.get(venue_id)
    db.session.query(Show).filter(Show.venue_id==venue_id).delete()
    name = venue.name
    db.session.delete(venue)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + name + ' could not be deleted.')
  else:
    flash('Venue ' + name+ ' deleted successfully')
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({"id":artist.id, "name" : artist.name})
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  searchby = request.form.get('searchby','')
  search = request.form.get('search_term', '')
  if(searchby=='area'):
    if ',' in search:
      cityName = search.split(',')[0]
      stateName = search.split(',')[1].replace(' ','')
      artists = Artist.query.filter(Artist.state.ilike("%" + stateName + "%")).filter(Artist.city.ilike("%" + cityName + "%")).all()
    else:
      artists = Artist.query.filter(Artist.state.ilike("%" + search + "%")).all()
      artists += Artist.query.filter(Artist.city.ilike("%" + search + "%")).all()
  else:
    artists = Artist.query.filter(Artist.name.ilike("%" + search + "%")).all()
  data = []
  for artist in artists:
    upcoming_shows = db.session.query(Show).join(Artist).filter(Artist.id==artist.id, Show.start_time > datetime.now()).count()
    data.append({
      "id" : artist.id,
      "name" : artist.name,
      "num_upcoming_shows" : upcoming_shows
    })
  response={
    "count": len(artists),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  past_shows = db.session.query(Show).join(Artist).filter(Artist.id==artist.id, Show.start_time < datetime.now()).all()
  past_shows_list = []
  for show in past_shows:
    venue = Venue.query.get(show.venue_id)
    dict1 = {
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    }
    past_shows_list.append(dict1)

  upcoming_shows = db.session.query(Show).join(Artist).filter(Artist.id==artist.id, Show.start_time > datetime.now()).all()
  upcoming_shows_list = []
  for show in upcoming_shows:
    venue = Venue.query.get(show.venue_id)
    dict1 = {
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    }
    upcoming_shows_list.append(dict1)
  
  data["past_shows"] = past_shows_list
  data["upcoming_shows"] = upcoming_shows_list
  data["past_shows_count"] = len(past_shows_list)
  data["upcoming_shows_count"] = len(upcoming_shows_list)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  form.state.data = artist.state
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.genres.data = artist.genres
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.genres = request.form.getlist('genres')
    artist.website = request.form['website']
    artist.seeking_description = request.form['seeking_description']
    if 'seeking_venue' not in request.form:
      artist.seeking_venue = False
    else:
      artist.seeking_venue = True
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  form.state.data = venue.state
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.genres.data = venue.genres
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.genres = request.form.getlist('genres')
    venue.website = request.form['website']
    venue.seeking_description = request.form['seeking_description']
    if 'seeking_talent' not in request.form:
      venue.seeking_talent = False
    else:
      venue.seeking_talent = True
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
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
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      genres = request.form.getlist('genres'),
      website = request.form['website'],
      seeking_description = request.form['seeking_description']
    )
    if 'seeking_venue' not in request.form:
      artist.seeking_venue = False
    else:
      artist.seeking_venue = True
    db.session.add(artist)
    db.session.commit()
  except Exception as e:
    print(e)
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error:
    #abort(400)
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return redirect(url_for('index'))


@app.route('/artists/<artist_id>/delete', methods=['POST'])
def delete_artist(artist_id):
  error = False
  name = ''
  try:
    artist = Artist.query.get(artist_id)
    db.session.query(Show).filter(Show.artist_id==artist_id).delete()
    name = artist.name
    db.session.delete(artist)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + name + ' could not be deleted.')
  else:
    flash('Artist ' + name+ ' deleted successfully')
  return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = db.session.query(Show,Artist,Venue).join(Artist,Venue).all()
  data=[]
  for show in shows:
    data.append({
      "venue_id": show[2].id,
      "venue_name": show[2].name,
      "artist_id": show[1].id,
      "artist_name": show[1].name,
      "artist_image_link": show[1].image_link,
      "start_time": show[0].start_time.strftime("%m/%d/%Y, %H:%M")
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  artists = Artist.query.all()
  form.artist_id.choices = [(artist.id, artist.name) for artist in artists]
  venues = Venue.query.all()
  form.venue_id.choices = [(venue.id, venue.name) for venue in venues]
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  date_format = '%Y-%m-%d %H:%M:%S'
  try:
    show = Show()
    show.artist_id = request.form['artist_id']
    show.venue_id = request.form['venue_id']
    show.start_time = datetime.strptime(request.form['start_time'], date_format)
    db.session.add(show)
    db.session.commit()
  except Exception as e:
    error = True
    print(f'Error ==> {e}')
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    flash('An error occurred. Show could not be listed.')
  else: 
    flash('Show was successfully listed!')
  return redirect(url_for('index'))

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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

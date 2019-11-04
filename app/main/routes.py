from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, json, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, EditAIDatasetForm, PostForm, SearchForm, MessageForm, PatientplaceofmedicalservicechoiceForm, YesnochoiceForm, WaypointForm, TriggerForm
from app.models import User, Waypoint, Post, Message, Notification, yesnochoice, patientplaceofmedicalservicechoice
from app.translate import translate
from app.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    convertJs=url_for("static",filename="js/convert.js")
    mainJs=url_for("static",filename="js/main_part.js")
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.body.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.body.data, author=current_user,
                    height=form.height.data, weight=form.weight.data, bmi=form.bmi.data, muac=form.muac.data, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url, convertJs=convertJs, mainJs=mainJs)


# Here is the Service Worker  . . . . ..  Route
@bp.route('/sw.js', methods=['GET'])
def sw():
    return current_app.send_static_file('/sw.js')





# Start Models for selectField -----------------------------------------

@bp.route('/yesno', methods=['GET', 'POST'])
@login_required
def yesno():
    convertJs=url_for("static",filename="js/convert.js")
    mainJs=url_for("static",filename="js/main_part.js")
    form = YesnochoiceForm()
    if form.validate_on_submit():
        
        yesnopost = yesnochoice(name=form.name.data,
                    extra=form.extra.data)
        db.session.add(yesnopost)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.yesno'))
   
    return render_template('add_yesno.html', title=_('Yes No choice'), form=form,
                           convertJs=convertJs, mainJs=mainJs)

@bp.route('/patientplaceofmedicalservice', methods=['GET', 'POST'])
@login_required
def patientplaceofmedicalservice():
    convertJs=url_for("static",filename="js/convert.js")
    mainJs=url_for("static",filename="js/main_part.js")
    form = PatientplaceofmedicalservicechoiceForm()
    if form.validate_on_submit():
        
        patientplaceofmedicalservicepost = patientplaceofmedicalservicechoice(name=form.name.data,
                    extra=form.extra.data)
        db.session.add(patientplaceofmedicalservicepost)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.patientplaceofmedicalservice'))
   
    return render_template('add_patientplaceofmedicalservice.html', title=_('Patient Place Of Medical Service'), form=form,
                           convertJs=convertJs, mainJs=mainJs)


# End Models for selectField -----------------------------------------



@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)

@bp.route('/patientusers') 
@login_required 
def patientusers(): 
    bootstrapsearchJs=url_for("static",filename="js/bootstraptablesearch/index.js")
    users = User.query.order_by(User.id.desc()).all() 
    return render_template('allpatients.html', title='Patients', users=users, bootstrapsearchJs=bootstrapsearchJs)


@bp.route('/delete/<username>')
@login_required
def deleteuser(username):
    user = User.query.filter_by(username=username).first_or_404()
    db.session.delete(user)
    db.session.commit()
    flash('Congratulations, you have deleted a user!')
            
    return render_template('allpatients.html', user=user)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.lon = form.lon.data
        current_user.lat = form.lat.data
        current_user.color = form.color.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.lon.data = current_user.lon
        form.lat.data = current_user.lat
        form.color.data = current_user.color
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/edit_ai_dataset', methods=['GET', 'POST'])
@login_required
def edit_ai_dataset():
    form = EditAIDatasetForm(current_user.username)
    if form.validate_on_submit():
        current_user.patientplaceofmedicalservice = form.patientplaceofmedicalservice.data
        current_user.typeofnearesthealthcenter = form.typeofnearesthealthcenter.data
        current_user.address = form.address.data
        current_user.famsize = form.famsize.data
        current_user.pstatus = form.pstatus.data
        current_user.medu = form.medu.data
        current_user.fedu = form.fedu.data
        current_user.mhealth = form.mhealth.data
        current_user.fhealth = form.fhealth.data
        current_user.mjob = form.mjob.data
        current_user.fjob = form.fjob.data
        current_user.reason = form.reason.data
        current_user.guardian = form.guardian.data
        current_user.traveltime = form.traveltime.data
        current_user.nursevisittime = form.nursevisittime.data
        current_user.mealsdaily = form.mealsdaily.data
        current_user.malnutritiontreatment = form.malnutritiontreatment.data
        current_user.siblingswithrelatedsickness = form.siblingswithrelatedsickness.data
        current_user.seizurespermonth = form.seizurespermonth.data
        current_user.durationofseizure = form.durationofseizure.data
        current_user.activitylevel = form.activitylevel.data
        current_user.behavioralproblems = form.behavioralproblems.data
        current_user.triggers = form.triggers.data
        current_user.screeningfailed = form.screeningfailed.data
        current_user.extranutritionalsupport = form.extranutritionalsupport.data
        current_user.famed = form.famed.data
        current_user.extrapaidsupport = form.extrapaidsupport.data
        current_user.famrelation = form.famrelation.data
        current_user.playout = form.playout.data
        current_user.seizurestatus = form.seizurestatus.data
        current_user.drugadministration = form.drugadministration.data
        current_user.schoolenrolment = form.schoolenrolment.data

        
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_ai_dataset'))
    elif request.method == 'GET':
        form.patientplaceofmedicalservice.data = current_user.patientplaceofmedicalservice
        form.typeofnearesthealthcenter.data = current_user.typeofnearesthealthcenter
        form.address.data = current_user.address
        form.famsize.data = current_user.famsize
        form.pstatus.data = current_user.pstatus
        form.medu.data = current_user.medu
        form.fedu.data = current_user.fedu
        form.mhealth.data = current_user.mhealth
        form.fhealth.data = current_user.fhealth
        form.mjob.data = current_user.mjob
        form.fjob.data = current_user.fjob
        form.reason.data = current_user.reason
        form.guardian.data = current_user.guardian
        form.traveltime.data = current_user.traveltime
        form.nursevisittime.data = current_user.nursevisittime
        form.mealsdaily.data = current_user.mealsdaily
        form.malnutritiontreatment.data = current_user.malnutritiontreatment
        form.siblingswithrelatedsickness.data = current_user.siblingswithrelatedsickness
        form.seizurespermonth.data = current_user.seizurespermonth
        form.durationofseizure.data = current_user.durationofseizure
        form.activitylevel.data = current_user.activitylevel
        form.behavioralproblems.data = current_user.behavioralproblems
        form.triggers.data = current_user.triggers
        form.screeningfailed.data = current_user.screeningfailed
        form.extranutritionalsupport.data = current_user.extranutritionalsupport
        form.famed.data = current_user.famed
        form.extrapaidsupport.data = current_user.extrapaidsupport
        form.famrelation.data = current_user.famrelation
        form.playout.data = current_user.playout
        form.seizurestatus.data = current_user.seizurestatus
        form.drugadministration.data = current_user.drugadministration
        form.schoolenrolment.data = current_user.schoolenrolment

        
    return render_template('edit_ai_dataset.html', title=_('Edit AI Dataset'), form=form)

# - - - - - AI DATASET: VIEW SEARCH / DELETE - - - - - - 

@bp.route('/aidatasets') 
@login_required 
def aidatasets(): 
    bootstrapsearchJs=url_for("static",filename="js/bootstraptablesearch/index.js")
    users = User.query.all() 
    return render_template('allaidatasets.html', title='AI Datasets', users=users, bootstrapsearchJs=bootstrapsearchJs)


# Note By default, the datasets are already there based on the fact that they are part of the registered user. : 


# - - - - - END Search Dataset - - - - - 


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


# Patient Map ..............
@bp.route('/patientmap')
@login_required
def patientmap():
    return render_template('/map/patientmap.html')


@bp.route('/patientapi', methods=['POST'])
@login_required
def patientapi():
    db_data = User.query.all()
    infornation_dic = {}
    infornation_list = []
    for data in db_data:
        infornation_dic['data'] = []
        infornation_dic['Name'] = data.username
        infornation_dic['Picture'] = data.picture
        infornation_dic['Color'] = data.color
        infornation_dic['Longitude'] = data.lon
        infornation_dic['Latitude'] = data.lat
        infornation_list.append(infornation_dic)
        infornation_dic = {}

    return json.dumps(infornation_list)    


#00000000OOOOOOOOhhhhhhhhhhh LARGE GEOJSON MAP!!!!!1

@bp.route("/geospatial")
@login_required
def geospatial():
    geospatialCss=url_for("static",filename="css/geojson/style.css")
    geospatialJs=url_for("static",filename="js/geojson/index.js")
    return render_template('/geojson/index.html', geospatialJs=geospatialJs, geospatialCss=geospatialCss)


# . . . . . . .  WAYPOINTS         ... . . . . . . .. . . . . 


@bp.route('/addwaypoints', methods=['GET', 'POST'])
@login_required
def addwaypoints():
    convertJs=url_for("static",filename="js/convert.js")
    mainJs=url_for("static",filename="js/main_part.js")
    form = WaypointForm()
    if form.validate_on_submit():
        
        waypoint = Waypoint(place=form.place.data, author=current_user, placelat=form.placelat.data,
                    placelon=form.placelon.data, tolon=form.tolon.data, tolat=form.tolat.data, description=form.description.data)
        db.session.add(waypoint)
        db.session.commit()
        flash(_('Your waypoint is now live!'))

    return render_template('add_waypoint.html', title=_('Waypoints'), form=form,
                           convertJs=convertJs, mainJs=mainJs)




@bp.route('/waypoints') 
@login_required 
def userwaypoints(): 
    bootstrapsearchJs=url_for("static",filename="js/bootstraptablesearch/index.js")
    waypoints = Waypoint.query.all() 
    return render_template('allwaypoints.html', title='Waypoints', waypoints=waypoints, bootstrapsearchJs=bootstrapsearchJs)



@bp.route('/delete/<waypoint>')
@login_required
def deletewaypoint(place):
    waypoint = Waypoint.query.filter_by(place=place).first_or_404()
    db.session.delete(waypoint)
    db.session.commit()
    flash('Congratulations, you have deleted a waypoint!')
            
    return render_template('allwaypoints.html', waypoint=waypoint)


@bp.route('/waypoints/<username>')
@login_required
def waypointuser(username):
    username = waypointuser
    user = User.query.filter_by(username=username).first_or_404()
    
    waypoints = user.waypoints.order_by(Waypoint.timestamp.desc())
    return render_template('waypoints.html', waypointuser=waypointuser, waypoints=waypoints)




# Waypoint Map ..............
@bp.route('/patientwaypointmap')
@login_required
def patientwaypointmap():
    return render_template('/waypointmap/patientwaypointmap.html')


@bp.route('/patientwaypointmapapi', methods=['POST'])
@login_required
def patientwaypointapi():

    
    db_data = Waypoint.query.all()
    infornation_dic = {}
    infornation_list = []
    for data in db_data:
        if data.user_id == current_user.id:
            infornation_dic['data'] = []
            infornation_dic['Name'] = data.place
            infornation_dic['Picture'] = data.picture
            infornation_dic['Color'] = data.color
            infornation_dic['Longitude'] = data.placelon
            infornation_dic['Latitude'] = data.placelat
            infornation_list.append(infornation_dic)
            infornation_dic = {}

    return json.dumps(infornation_list)
  

#/** 
#@bp.route('/patientmap')
#@login_required
#def patientmap():
#    return render_template('/map/patientmap.html')


#@bp.route('/patientapi', methods=['POST'])
#@login_required
#def patientapi():
#    db_data = User.query.all()
#    infornation_dic = {}
#    infornation_list = []
#    for data in db_data:
#        infornation_dic['data'] = []
#        infornation_dic['Name'] = data.username
#        infornation_dic['Picture'] = data.picture
#        infornation_dic['Color'] = data.color
#        infornation_dic['Longitude'] = data.lon
#        infornation_dic['Latitude'] = data.lat
#        infornation_list.append(infornation_dic)
#        infornation_dic = {}

#    return json.dumps(infornation_list)    
#**/
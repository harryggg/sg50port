import webapp2
import cgi
import datetime
import jinja2

import os

from google.appengine.api import mail

from google.appengine.ext import db
import google.appengine.ext.db
from google.appengine.api import users

JINJA_ENVIRONMENT = jinja2.Environment(
		loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
		extensions=['jinja2.ext.autoescape'],
		autoescape=True)

class Ticket(db.Expando):
	ticketid = db.StringProperty()
	departureTime = db.DateTimeProperty()
	name = db.StringProperty()
	customerName = db.StringProperty()
	checkedin = db.BooleanProperty()

class Index(webapp2.RequestHandler):
	def get(self):
		template_values={}
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values)) 

class CustomerPanel(webapp2.RequestHandler):
	def get(self):
		template_values={}
		template = JINJA_ENVIRONMENT.get_template('CustomerPanel.html')
		self.response.write(template.render(template_values))

class GetQR(webapp2.RequestHandler):
	def get(self):
		currentTicket = Ticket.gql("WHERE ticketid = '%s'"%(self.request.get('ticketid'))).get()
		template_values={"ticket":currentTicket}
		template = JINJA_ENVIRONMENT.get_template('QRdisplay.html')
		self.response.write(template.render(template_values))

class verifyQR(webapp2.RequestHandler):
	def post(self):
		QRcode = self.request.get('qrcode')
		currentTicket = Ticket.gql("WHERE ticketid = '%s'"%(QRcode.split('#')[1])).get()
		template_values={"ticket":currentTicket}
		if currentTicket:
			isValid = (currentTicket.departureTime - (datetime.datetime.now()+datetime.timedelta(hours=8) )  <= datetime.timedelta(hours=5)) and (currentTicket.departureTime - (datetime.datetime.now()+datetime.timedelta(hours=8) )>datetime.timedelta(hours=0))
			template_values["isValid"]=isValid
			if not isValid:
				template_values["validFrom"]=(currentTicket.departureTime-datetime.timedelta(hours=5)).strftime("%d/%m/%Y %H:%M")
				template_values["validTo"]=currentTicket.departureTime.strftime("%d/%m/%Y %H:%M")
		template = JINJA_ENVIRONMENT.get_template('QRshop.html')
		self.response.write(template.render(template_values))



class ShopPanel(webapp2.RequestHandler):
	def get(self):
		template_values={}
		template = JINJA_ENVIRONMENT.get_template('ShopPanel.html')
		self.response.write(template.render(template_values))


class AdminPanel(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			url_link = users.create_logout_url(self.request.uri)
			linktext = 'Logout'
			
		else:
			url_link = users.create_login_url(self.request.uri)
			linktext = 'Login'
		template_values = {
				'urllink':url_link,
				'linktext':linktext,
				'isadmin':users.is_current_user_admin()
			}
		template = JINJA_ENVIRONMENT.get_template('AdminPanel.html')
		self.response.write(template.render(template_values))

class CreateTicketPanel(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user and users.is_current_user_admin():
			template_values = {
				'tickets':Ticket.all(),
				
			}
			template = JINJA_ENVIRONMENT.get_template('CreateTicketPanel.html')
			self.response.write(template.render(template_values))
			
		else:
			self.redirect('/admin')

class CreateTicket(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user and users.is_current_user_admin():
			new_ticket=Ticket()
			new_ticket.ticketid = self.request.get("ticketid")
			new_ticket.name = self.request.get("name")
			new_ticket.customerName = self.request.get("customerName")
			new_ticket.departureTime = datetime.datetime.strptime(self.request.get("departureTime"), "%d/%m/%Y %H:%M")
			new_ticket.checkedin = False
			new_ticket.put()

			self.redirect('/createTicketPanel')
			
		else:
			self.redirect('/admin')

class DeleteTicket(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		if user and users.is_current_user_admin():
			ticket = db.get(self.request.get("ticketkey"))
			ticket.delete()

			self.redirect('/createTicketPanel')
			
		else:
			self.redirect('/admin')

class CheckinPanel(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user and users.is_current_user_admin():
			template_values = {
				
			}
			template = JINJA_ENVIRONMENT.get_template('checkinPanel.html')
			self.response.write(template.render(template_values))
			
		else:
			self.redirect('/admin')

class VerifyQRForCheckin(webapp2.RequestHandler):
	def post(self):
		QRcode = self.request.get('qrcode')
		currentTicket = Ticket.gql("WHERE ticketid = '%s'"%(QRcode.split('#')[1])).get()
		template_values={"ticket":currentTicket}
		if currentTicket:
			isValid = currentTicket.departureTime - (datetime.datetime.now()+datetime.timedelta(hours=8) )<= datetime.timedelta(minutes=30)
			template_values["isValid"]=isValid
			if isValid:
				currentTicket.checkedin = True
				currentTicket.put()
			else:
				template_values["validFrom"]=(currentTicket.departureTime-datetime.timedelta(minutes=30)).strftime("%d/%m/%Y %H:%M")

		template = JINJA_ENVIRONMENT.get_template('QRcheckin.html')
		self.response.write(template.render(template_values))

class ExpressPanel(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user and users.is_current_user_admin():
			template_values = {
				
			}
			template = JINJA_ENVIRONMENT.get_template('ExpressPanel.html')
			self.response.write(template.render(template_values))
			
		else:
			self.redirect('/admin')

class VerifyQRForExpress(webapp2.RequestHandler):
	def post(self):
		QRcode = self.request.get('qrcode')
		currentTicket = Ticket.gql("WHERE ticketid = '%s'"%(QRcode.split('#')[1])).get()
		template_values={"ticket":currentTicket}
		if currentTicket:
			
			template_values["isValid"] = currentTicket.checkedin
	

		template = JINJA_ENVIRONMENT.get_template('QRexpress.html')
		self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
		('/',Index),
		('/customer',CustomerPanel),
		('/getQR',GetQR),
		('/admin',AdminPanel),
		('/shop',ShopPanel),
		('/verifyQR',verifyQR),
		('/createTicketPanel',CreateTicketPanel),
		('/createTicket',CreateTicket),
		('/deleteTicket',DeleteTicket),
		('/checkinPanel',CheckinPanel),
		('/verifyQRForCheckin',VerifyQRForCheckin),
		('/expressPanel',ExpressPanel),
		('/verifyQRForExpress',VerifyQRForExpress)
   
														
], debug=True)

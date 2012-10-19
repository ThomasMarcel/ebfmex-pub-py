import json
from datetime import datetime, timedelta

from google.appengine.ext import webapp
from google.appengine.ext import db

from models import *

class search(webapp.RequestHandler):
	def get(self):
		gvalue = self.request.get('value')
		gfield = self.request.get('field')
		gkind = self.request.get('kind')
		self.response.headers['Content-Type'] = 'text/plain'
		if not gvalue or gvalue == '':
			errordict = {'error': -1, 'message': 'Correct use: /backend/search?value=<str>[&kind=<str>&field=<str>]'}
                        self.response.out.write(json.dumps(errordict))
		else:
			search = SearchData.all().filter("Value =", gvalue)
			if gfield and gfield != '':
				search.filter("Field =", gfield)
			if gkind and gkind != '':
				search.filter("Kind =", gkind)
			found = False
			resultlist = []
			try:
				for result in search:
					found = True
					if gkind == 'Oferta':
						#self.response.out.write('gkind: ' + gkind + ' gvalue: ' + gvalue + '\n')
						oferta = Oferta.get_by_id(int(result.Sid))
						ofertadict = {'IdOft': oferta.IdOft, 'IdEmp': oferta.IdEmp, 'IdCat': oferta.IdCat, 'Oferta': oferta.Oferta, 'Descripcion': oferta.Descripcion}
						resultlist.append(ofertadict)
					elif gkind == 'Empresa':
						empresa = Empresa.get_by_id(int(result.Sid))
						empresadict = {'IdEmp': empresa.IdEmp, 'Nombre': empresa.Nombre, 'Desc': Desc, 'OrgEmp': empresa.OrgEmp}
						resultlist.append(empresadict)
					elif gkind == 'Sucursal':
						sucursal = Sucursal.get_by_id(int(result.Sid))
						sucursaldict = {'IdSuc': sucursal.IdSuc, 'Nombre': sucursal.Nombre, 'IdEmp': sucursal.IdEmp, 'Geo1': sucursal.Geo1, 'Geo2': sucursal.Geo2, 'direccion': {'DirCalle': sucursal.DirCalle, 'DirCol': sucursal.DirCol, 'DirCp': sucursal.DirCp, 'DirEnt': sucursal.DirEnt, 'DirMun': sucursal.DirMun}, 'Tel': sucursal.Tel} 
						resultlist.append(sucursaldict)
					else:
						resultdict = {'Sid': result.Sid, 'Value': result.Value, 'Kind': result.Kind, 'Field': result.Field}
						resultlist.append(resultdict)
				if not found:
					errordict = {'error': -2, 'message': 'No result found for search " ' + gvalue + '"'}
		                        self.response.out.write(json.dumps(errordict))
				else:
					self.response.out.write(json.dumps(resultlist))
			except AttributeError:
				errordict = {'error': -1, 'message': 'Datastore inconsistency.'}
				self.response.out.write(json.dumps(errordict))

class generatesearch(webapp.RequestHandler):
	def get(self):
		kindg = self.request.get('kind')
		field = self.request.get('field')
		gid = self.request.get('id')
		gvalue = self.request.get('value')
		genlinea = self.request.get('enlinea')
		self.response.headers['Content-Type'] = 'text/plain'
		if not kindg or not field or kindg == '' or field == '':
			errordict = {'error': -1, 'message': 'Correct use: /backend/generatesearch?kind=<str>&field=<str>[&id=<int>&value=<str>&entidad=<str>&enlinea=<int>]'}
			self.response.out.write(json.dumps(errordict))
		elif gid and gid != '' and gvalue and gvalue != '':
			existsQ = SearchData.all().filter("Kind = ", kindg).filter("Sid = ",sid).filter("Field = ",field)
			if genlinea:
				existsQ.filter("Enlinea =", genlinea)
			for searchdata in existsQ:
				db.delete(searchdata)
			values = gvalue.replace('.',' ').replace(',',' ').split(' ')
			for value in values:
				if len(value) > 3:
					sd = SearchData()
					sd.Sid = gid
					sd.Kind = kindg
					sd.Field = field
					sd.Value = value
					if genlinea:
						sd.Enlinea = genlinea
					sd.put()
		else:
			try:
				kindsQ = db.GqlQuery("SELECT * FROM " + kindg)
				kinds = kindsQ.run(batch_size=100000)
				for kind in kinds:
					#self.response.out.write("1")
					values = getattr(kind, field)
					values = values.replace('.',' ').replace(',',' ').split(' ')
					for value in values:
						if len(value) > 3:
							exists = False
							existsQ = SearchData.all().filter("Kind = ",kindg).filter("Sid = ",str(kind.key().id())).filter("Field = ",field).filter("Value = ", value)
							existsR = existsQ.run(limit=1)
							for searchdata in existsR:
								exists = True
							if not exists:
								#self.response.out.write("2")
								newsd = SearchData()
								newsd.Sid = str(kind.key().id())
								newsd.Kind = kindg
								newsd.Field = field
								newsd.Value = value
								newsd.FechaHora = datetime.now()
                       				                if genlinea:
                                                			newsd.Enlinea = genlinea
								newsd.put()
			except db.KindError:
				errordict = {'error': -2, 'message': 'Kind ' + kind + ' couldn\'t be found. Careful it is case sensitive.'}
	                        self.response.out.write(json.dumps(errordict))
			except AttributeError:
				errordict = {'error': -2, 'message': 'Kind ' + kindg+ ' doesn\'t have any attribute ' + field + '. Careful it is case sensitive.'}
                                self.response.out.write(json.dumps(errordict))

class SearchKeyword(webapp.RequestHandler):
	def get(self):
		keyword = self.request.get('keyword')
		results = self.request.get('results')
		page = self.request.get('page')
                self.response.headers['Content-Type'] = 'text/plain'
                if not keyword or not results or not page:
                        errordict = {'error': -1,'message': 'Correct use: /search/keyword?keyword=<str>&results=<int>[&page=<int>'}
                        self.response.out.write(json.dumps(errordict))
                else:
                        if not page or page == '':
                                page = 1
                        page = int(page)
                        if page > 0:
                                page -= 1
                                page *= int(results)
                        keyword = keyword.lower()
                        keywordsQ = db.GqlQuery("SELECT * FROM OfertaPalabra WHERE Palabra = :1 ORDER BY FechaHora DESC", keyword)
                        keywords = keywordsQ.fetch(results, offset=page)
                        idofts = []
                        for keyword in keywords:
                                idofts.append(keyword.IdOft)
                        ofertasQ = db.GqlQuery("SELECT * FROM Oferta WHERE IdOft IN :1", idofts)
                        ofertas = ofertasQ.fetch(results)
                        ofertalist = []
                        for oferta in ofertas:
                                #self.response.out.write("1")
                                ofertadict = {}
                                ofertadict['id'] = oferta.IdOft
                                tipo = None
                                if oferta.Descuento == '' or oferta.Descuento == None:
                                        tipo = 1
                                else:
                                        tipo = 2
                                ofertadict['tipo_oferta'] = tipo
                                ofertadict['oferta'] = oferta.Oferta
                                ofertadict['descripcion'] = oferta.Descripcion
                                ofertadict['url_logo'] = 'http://' + APPID + '/ofimg?id=' + oferta.IdOft
                                suclist = []
                                sucursalQ = db.GqlQuery("SELECT * FROM OfertaSucursal WHERE IdOft = :1", oferta.IdOft)
                                sucursales = sucursalQ.run(batch_size=100)
                                for suc in sucursales:
                                        sucdict = {'id': suc.IdSuc, 'lat': suc.Lat, 'long': suc.Lng}
                                        suclist.append(sucdict)
                                ofertadict['sucursales'] = suclist
                                empQ = db.GqlQuery("SELECT * FROM Empresa WHERE IdEmp = :1", oferta.IdEmp)
                                empresas = empQ.fetch(1)
                                emplist = {}
                                for empresa in empresas:
                                        emplist['id'] = empresa.IdEmp
                                        emplist['nombre'] = empresa.Nombre
                                ofertadict['empresa'] = emplist
                                ofertadict['ofertas_relacionadas'] = randOffer(3,oferta.IdEmp)
                                ofertalist.append(ofertadict)
                        self.response.out.write(json.dumps(ofertalist))

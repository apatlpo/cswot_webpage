# -*- coding: utf-8 -*-
"""
@brief RECUPERATION DES POSITIONS GPS DES BALISES IRIDIUM NOVATECH de type MMI-513-00000

Alternative à LOPSTRACK lorsque l'accès au réseau local Ifremer n'est pas possible ou difficile

@author: Michel HAMON 12/01/2023
"""
# imports
import struct
import datetime
import time
import os
import imaplib
import email
try:
    # for opencpn
    import gpxpy
    #library for encoding AIS sentences sent to 
    import aislib
    # Library to communicate locations to opencpn through UDP
    import socket
    #UDP IP and Port that opencpn is listening to (localhost)
    UDP_IP = "127.0.0.1"
    UDP_PORT = 5005
except:
    gpxpy=None
    aislib=None
    socket=None
try:
    import simplekml
except:
    simplekml=None
import math


class NOVATECH:
    """ La classe NOVATECH permet de lire une boite mail ifremer sur laquelle arrivent les messages des balises NOVATECH iridium 
    (Ne pas utiliser la boite mail planeurs réservé à LOPSTRACK)
    Lors de l'activation des balises Novatech sur le site Metocean, mettre son adresse mail ifremer en destinataire\n
    La méthode Read_Ifremer_Inbox_mail permet d'aller récupérer tous les messages reçus des balises dans sa boite de réception
    et de les stocker sur son PC dans le répertoire rentré en paramètre. Un sous répertoire ayant pour nom le numéro IMEI est 
    créé pour chaque balise. Une fois que les mails ont été correctement lus et enregistrés sur le PC, il est conseillé de les 
    effacer de sa boite mail afin de ne pas les relire de nouveau lors des prochaines interrogations.\n
    La méthode Extract_All_Positions(IMEI) permet ensuite de traiter tous les fichers récupérés sur son PC pour une balise iridium donnée,
    d'en extraire les positions GPS en les affichant sur le terminal et au final de générer 3 types de ficher (texte, gpx et kml)\n
    La méthode OpenCPN_Plot_Last_Position(IMEI) permet de tracer le dernier point reçu par la balise IMEI sur OpenCPN
    """
    def __init__(self,local_working_directory):
        """Constructeur
        @param local_working_directory définit le répertoire de travail sur le PC où seront stockés les fichiers
        """
        self.local_directory = local_working_directory

    def Read_Ifremer_Inbox_mail(self,login,pwd):
        """ Interroge la boite mail ifremer, 
        parcourt la boite inbox en recherchant les messages ayant pour objet "SBD Msg From Unit: xxxxxxIMEIxxxxx" \n
        récupère le fichier joint ayant pour extension .sbd \n
        et le sauvegarde dans le sous répertoire local_working_directory/xxxxxxIMEIxxxxx \n
        @param login  login intranet ifremer
        @param pwd    mot de passe intranet ifremer
        """
        try:
            server = imaplib.IMAP4_SSL('eusa.ifremer.fr', 993)
        except imaplib.IMAP4.error:
            print("pb login serveur")
            return
        server.login(login, pwd)
        server.select()
        typ, data = server.search(None,  '(FROM "sbdservice@sbd.iridium.com")')
        for num in data[0].split():
            typ, data = server.fetch(num, '(RFC822)')
            email_body = data[0][1] #récupère le contenu du mail
            mail = email.message_from_string(email_body.decode())
            #Vérifie si il y a une pièce jointe
            if mail.get_content_maintype() != 'multipart':	
                continue   			
            IMEI = mail["Subject"].split(": ")[1] #On récupère le numéro IMEI depuis le sujet
            #Détermine le dossier de destination de la pièce jointe
            detach_dir =self.local_directory + IMEI 
            if not os.path.exists(detach_dir) :
                os.mkdir(detach_dir)
            #récupère la pièce jointe
            # we use walk to create a generator so we can iterate on the parts and forget about the recursive headache
            for part in mail.walk():
                # multipart are just containers, so we skip them
                if part.get_content_maintype() == 'multipart':
                    continue
                # is this part an attachment ?
                if part.get_content_type() == "text/plain" :
                    continue
                filename = part.get_filename()
                # if there is no filename, skip the part
                if not filename:
                    continue
                att_path = os.path.join(detach_dir, filename)
                print (att_path)
                #Si le fichier existe déjà, passe au suivant
                if os.path.isfile(att_path) :
                    continue
                # finally write the stuff
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()
    #       if 'OK'==server.copy(num,'BALISES_NOVATECH')[0]:
    #                   # remove it from inbox
    #           server.store(num,'+FLAGS','\\Deleted')

        #Ferme la connexion
        server.close()
        server.logout()


    def Extract_Position(self,filename):
        """ Extrait l'heure, la latitude et la longitude du fichier binaire reçu par les balises Novatech
        Pour le détail du décodage, voir p32 du manuel
        @param filename nom du fichier à traiter
        @return timestamp, latitude et longitude en degrés si ok, None, None, None sinon
        """
        if filename.split('.')[-1]=='sbd' and os.path.getsize(filename) == 19:
            f=open(filename,"rb")
            Data_SBD=f.read()
            f.close()
            s=struct.Struct(">BBB") 
            Header_Data=s.unpack(Data_SBD[0:3])
            CMD_TYPE=Header_Data[0]
            CMD_SUB_TYPE=Header_Data[1]
            SEQ_NUM=Header_Data[2]
            if CMD_TYPE==0x01 and CMD_SUB_TYPE==0xfd and SEQ_NUM==0x00:
                s=struct.Struct(">IBIIBBB")
                T_POSITION_REPORT_DATA=s.unpack(Data_SBD[3:19])
                GPS_TIME=T_POSITION_REPORT_DATA[0]+time.mktime(datetime.datetime.strptime("06/01/1980 00:00:00", "%d/%m/%Y %H:%M:%S").timetuple())
                RECORD_TYPE=(T_POSITION_REPORT_DATA[1]&0x80)>>7
                RESERVED=(T_POSITION_REPORT_DATA[1]&0x40)>>6
                NUMBER_SATS_VISIBLE=((T_POSITION_REPORT_DATA[1]&0x38)>>3) +3 
                HDOP=(T_POSITION_REPORT_DATA[1]&0x07)*0.5
                GPS_LATITUDE=T_POSITION_REPORT_DATA[2]*0.000001-90
                GPS_LONGITUDE=T_POSITION_REPORT_DATA[3]*0.000001-180
                SPEED=T_POSITION_REPORT_DATA[4]
                GPS_FIX_ACCURACY=T_POSITION_REPORT_DATA[4]
                TIME_TO_FIX=T_POSITION_REPORT_DATA[5]
                if RECORD_TYPE==1:
                    return GPS_TIME, GPS_LATITUDE, GPS_LONGITUDE
        return None, None, None

    def Extract_Last_Position(self,IMEI):
        """ Recherche le dernier fichier binaire Novatech .sbd reçu dans le sous répertoire xxxxxxIMEIxxxxx,\n
        en extrait l'heure, longitude et latitude,\n
        @param  IMEI   numéro IMEI de la balise à analyser
        @return timestamp, latitude et longitude en degrés si ok, None, None, None sinon
        """
        directory = self.local_directory + IMEI
        if not (os.path.exists(directory)):
            print("Directory does not exists")
            return None,None,None
        dirs=os.listdir(directory)
        dirs.sort()
        Last_SBD = dirs[-1]
        print("Last SBD : " + Last_SBD) 
        t_Last_SBD, lat_Last_SBD, lon_Last_SBD = self.Extract_Position(directory + '//' + Last_SBD)
        return t_Last_SBD, lat_Last_SBD, lon_Last_SBD


    def dec2DM(self,gps,type):
        """converts gps decimal format to a minutes format ## example of argument : 48.456218, lat
        @param gps : float that represents the decimal value of one GPS coordinate
        @param type : string 'lat' or 'lon'
        """
        try : 
            ref = 'REF_ERROR'
            absgps = abs(gps)
            degrees = math.floor(absgps)
            dec = absgps - degrees
            degrees = str(degrees)
            totalminutes = dec*60.0
            minutes = str(round(math.fmod(totalminutes,60),2))
            if type == 'lat':
                if gps>=0:
                    ref = 'N'
                else:
                    ref = 'S'
            if type == 'lon':
                if gps>=0:
                    ref = 'E'
                else:
                    ref = 'W'
            return degrees + '°' + minutes + '\''  + ref
        except :
            return '' 

    def Extract_All_Positions(self,IMEI):
        """ Analyse tous les fichiers binaire Novatech .sbd présents dans le sous répertoire xxxxxxIMEIxxxxx,
        en extrait les heures, longitudes et latitudes,\n
        crée un fichier texte xxxxxxIMEIxxxxx.txt,\n
        crée un fichier gpx xxxxxxIMEIxxxxx.gpx lisible par OpenCPN,\n
        #crée un fichier kml xxxxxxIMEIxxxxx.kml lisible par google earth\n
        @param  IMEI   numéro IMEI de la balise à analyser
        """
        # Creating a new gpx file:
        gpx = gpxpy.gpx.GPX()
        # Create first track in our GPX:
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)
        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        Liste_points_kml = []
        directory = self.local_directory + IMEI
        if not (os.path.exists(directory)):
            print("Directory does not exists")
            return
        dirs=os.listdir(directory)
        dirs.sort()
        filename = directory+'\\' + str(IMEI)
        print(filename)
        f_text=open(filename + '.txt','w')        
        for fichier in dirs: 
            t, lat, lon = self.Extract_Position(directory+'\\' + fichier)
            if t != None:
                Liste_points_kml.append((lon,lat))
                #point = LatLon(lat,lon)
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, time = datetime.datetime.fromtimestamp(t)))
                String_result = (datetime.datetime.fromtimestamp(t).strftime('%d/%m/%Y %H:%M:%S') + "\t" 
                                + ('%.6f'%lat) + "\t"
                                + ('%.6f'%lon) + "\t"
                                + self.dec2DM(lat,"lat") + "\t"
                                + self.dec2DM(lon, "lon"))
                print(String_result)
                f_text.write( String_result + '\n')
        f_text.close()
        #
        f_gpx = open(filename + '.gpx', "w") 
        f_gpx.write( gpx.to_xml())
        f_gpx.close()
        #
        kml = simplekml.Kml()
        ls=kml.newlinestring(name=str(IMEI), description="Balise Iridium",coords=Liste_points_kml)
        ls.style.linestyle.width = 1    
        kml.newpoint(name=str(IMEI),coords=[Liste_points_kml[-1]])     
        kml.save(filename + '.kml') 


    def OpenCPN_Plot_Last_Position(self,IMEI):
        """ Recherche le dernier fichier binaire Novatech .sbd reçu dans le sous répertoire xxxxxxIMEIxxxxx,\n
        en extrait l'heure, longitude et latitude,\n
        fabrique un message AIS et l'envoie sur une socket (@IP127.0.0.1, UDP, port 5005).\n
        Configurer OpenCPN pour qu'il soit à l'écoute (Sous OpenCPN options/connections/add connection :\n
            select Network, protocol : UDP, Address = 127.0.0.1, Network port = 5005)
        """
        t_Last_SBD, lat_Last_SBD, lon_Last_SBD  = self.Extract_Last_Position(IMEI)
        if t_Last_SBD == None:
            return
        datetime_t = datetime.datetime.fromtimestamp(t_Last_SBD)
        aismsg = aislib.AISStaticAndVoyageReportMessage(
            mmsi = int(str(IMEI)[6:16]),
            shipname = 'NOVATECH', shiptype=30,                 
            month = datetime_t.month,
            day = datetime_t.day, 
            hour = datetime_t.hour, 
            minute = datetime_t.minute)
        ais = aislib.AIS(aismsg)
        payload = ais.build_payload(False)
        MESSAGE = bytes(payload, 'utf8')
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
        aismsg = aislib.AISPositionReportMessage(
            mmsi = int(str(IMEI)[6:16]),
            status = 8,
            sog = 0,
            pa = 1,
            lon = lon_Last_SBD*60*10000,
            lat = lat_Last_SBD*60*10000,
            cog = 0000,
            ts = 25,
            raim = 1,
            comm_state = 82419   
        )
        ais = aislib.AIS(aismsg)
        payload = ais.build_payload(False)
        MESSAGE = bytes(payload, 'utf8')
        sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
        sock.close()
        

if __name__ == "__main__":
    
    login_intranet_ifremer = "xxxxxx"
    mot_de_passe_intranet_ifremer = "xxxxxxx"
    # Instanciation de la classe NOVATECH en précisant le répertoire de travail sur son PC
    balise_iridium = NOVATECH("C:\\Users\\Administrateur\\Desktop\\WAAXT2023\\Iridium\\")
    # Interrogation de la boite mail Ifremer avec login et mot de passe intranet
    balise_iridium.Read_Ifremer_Inbox_mail(login_intranet_ifremer,mot_de_passe_intranet_ifremer)
    # Extraction des positions reçues avec tous les fichiers présents dans le sous répertoire IMEI.
    # Les positions sont affichées dans le terminal. Des fichiers IMEI.txt, IMEI.gpx, IMEI.kml sont créés dans le sous répertoire IMEI
    balise_iridium.Extract_All_Positions("300434063369340")
    #balise_iridium.Extract_All_Positions("300434063363300")
    balise_iridium.OpenCPN_Plot_Last_Position("300434063369340")

    # # extraction de la date et position d'un message sbd reçu
    t_pos, lat, lon = balise_iridium.Extract_Position("C:\\Users\\Administrateur\\Desktop\\WAAXT2023\\Iridium\\300434063369340\\300434063369340_002132.sbd")
    # # Affichage en degrés
    print(datetime.datetime.fromtimestamp(t_pos).strftime('%d/%m/%Y %H:%M:%S') + "\t" + ('%.6f'%lat) + "\t"+ ('%.6f'%lon))
    # # En degrés minute seconde décimal
    print(datetime.datetime.fromtimestamp(t_pos).strftime('%d/%m/%Y %H:%M:%S') + "\t" + balise_iridium.dec2DM(lat,"lat") + "\t"+ balise_iridium.dec2DM(lon,"lon"))





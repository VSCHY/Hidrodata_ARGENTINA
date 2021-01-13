from selenium import webdriver
import time
import sys
import pandas as pd
import datetime


def createDataframeStations(L):
   df = pd.DataFrame(L)
   df.index = df["Codigo"]
   for varn in ["Alta", "Registro", "RegistroValidoHasta"]:
      df[varn] = df[varn].apply(lambda x: x.replace("/Date(","").replace(")/",""))

      df[varn] = df[varn].apply(lambda x: datetime.datetime.fromtimestamp(int(x)/1000))
   return df

######################################################

class SNIH:
   def __init__(self, dir_out):
   
      self.initialization(dir_out)
      self.acceptTerms()
      # Consider inactivate stations
      self.exScript("document.querySelector('#filtroInactivas').click()")
      time.sleep(1)
      
   
   def initialization(self, dir_out):
      fp= webdriver.FirefoxProfile() 
      fp.set_preference("browser.download.folderList", 2)
      fp.set_preference("browser.download.manager.showWhenStarting", False)
      fp.set_preference("browser.download.dir", dir_out)
      fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
      fp.set_preference("dom.webdriver.enabled", False)

      my_url = "https://snih.hidricosargentina.gob.ar/Inicio.aspx"
      options = webdriver.FirefoxOptions()
      options.add_argument('headless')
      #
      self.driver = webdriver.Firefox(firefox_profile=fp, options=options)
      self.driver.get(my_url)     
      #
      self.wait_load_items("CBIngresar")
      
   def acceptTerms(self):
      self.exScript("document.querySelector('#CBIngresar').checked = true")
      self.exScript("AceptaTerminos();")
      self.exScript("document.querySelector('#btnIngresar').click()")
      #
      self.wait_load_items("accordian")
      self.wait_cursor()
      
   ######################################################

   def getListaEstaciones(self, var, varValues):
      """
      For Caudal : var = "Tipo"; varValues = ["HA", "M", "HM", "HMA"]
      """
      self.var = var
      self.varValues = varValues
      #
      self.listaEstaciones = self.exScript("return listaEstacionesCompleta")
      self.EST = {el["Codigo"]: el for el in self.listaEstaciones}
      self.ESTindex = {el["Codigo"]: k for k, el in enumerate(self.listaEstaciones)}

      self.subselection = {key:self.EST[key]
                         for key in self.EST.keys()
                         if ((self.EST[key][var] in varValues) and (self.EST[key]["Area"] > 5000 ))}
      
      # Reference in the map.entities
      lenmap = self.exScript("return map.entities.getLength()")
      self.ENTITIES_ref = {int(self.exScript("return map.entities.get({0}).metadata.description".format(num))):num for num in range(0,lenmap)}
      
   ######################################################

   def exScript(self, script):
      A = self.driver.execute_script(script)
      return A

   def wait_load_items(self, identity, which = "id"):
       n = 1
       p = 1
       while p: 
           try:
               if which == "id":
                  self.driver.find_element_by_id(identity)
               elif which == "xpath":
                  self.driver.find_element_by_xpath(identity)
               p = 0
           except:
               time.sleep(3)
               n += 1
           if n == 60:
               print('Time limit exceeded.')
               break     
               
   def wait_cursor(self):
      go = False
      i = 1 
      while not go:
         out = self.driver.execute_script("return document.getElementById('form1').style.cursor")
         if out == "default":
            go = True
         else:
            i += 1
            time.sleep(3) 
         if i > 60: 
            print("Blocked in loop")
            sys.exit()         
   
   ######################################################  

   def metaStationsDataframe(self, nameFull, nameSubselection):
      """
      nameFull = "BDHI_Estaciones_RedHidNac_full.csv"
      nameSubselection = "BDHI_Estaciones_RedHidNac_selectionCaudal.csv"
      """
      FullST = []
      for el in self.listaEstaciones:
         FullST.append(el)
      SubST = []
      for el in self.listaEstaciones:
         if el[self.var] in self.varValues:
            SubST.append(el)
      df = createDataframeStations(FullST)
      df = df.to_csv(nameFull, sep = ";")

      df = createDataframeStations(SubST)
      df = df.to_csv(nameSubselection, sep = ";")
      
   ######################################################

   def download_st(self, index):
      print("Station:", self.EST[index]["Lugar"])
      ref = str(self.ENTITIES_ref[index])
      self.goToStation(ref)
      meanDis = self.goToData()

      if meanDis:
         self.setParam()        
         self.exScript("mostrarDatosHistoricos()")
         self.wait_cursor()
         table = self.exScript("return document.querySelector('#tabla3').innerHTML")
         if table == "No se encontraron datos":
            print("Discharge Section accessible but NO DATA")
         else:
            self.wait_load_items("captionHistorico")
            self.exScript("document.querySelector('#captionHistorico > button').click()")
            time.sleep(2)
         self.exitStation()
         print("-> Success")
      else:
         self.exitStation()
         print("-> Variable Mean Monthly Discharge not available")
      print("")

   def goToStation(self, ref):
      self.driver.switch_to.default_content()
      a = self.exScript("return map.entities.get({0}).metadata".format(ref))
      self.exScript("var estacionSeleccionada = listaEstacionesCompleta.find(elementoEstacion => elementoEstacion.Codigo == map.entities.get({0}).metadatadescription);".format(ref))
      CLICK = "Microsoft.Maps.Events.invoke(map.entities.get("+ref+"), 'click', {target:map.entities.get("+ref+")});"
      self.exScript(CLICK)
      time.sleep(2)
      self.wait_cursor()
      
   def goToData(self):
      """
      The last part of this function is used to verify there is monthly mean discharge data
      Which corresponds to value 102
      """
      self.driver.switch_to.frame('frameMuestraDatos')
      self.exScript("document.getElementById('li1').children[0].click()")
      self.wait_cursor()
      self.exScript("document.querySelector('#cbTipoParametros').value = 1")
      self.exScript("eventoSeleccionaTipoParametro()")
      self.wait_cursor()
      A = self.exScript("return document.querySelector('#cbParametros').options")
      meanDis = False
      for i in range(1,len(A)):
         val = self.exScript("return document.querySelector('#cbParametros').options[{0}].value".format(i))
         if int(val) == 102:
            meanDis = True
      return meanDis
      
   def setParam(self):
      """
      Here for Mean Monthly Discharge -> Value = 102
      """ 
      self.exScript("document.querySelector('#cbParametros').value = 102")
      self.exScript("eventoSeleccionaParametro()")
      time.sleep(2)
      self.exScript("return document.querySelector('#fechaDesde').value")
      self.exScript("document.querySelector('#fechaDesde').value = '2000-01-01'")
      self.exScript("eventoSeleccionaParametro();")
      self.exScript("document.querySelector('#fechaHasta').value = '2009-01-01'")
      self.exScript("eventoSeleccionaParametro();")
      self.wait_cursor()
      
   def exitStation(self):
      self.driver.switch_to.default_content()
      self.exScript("document.querySelector('#botonCerrar').click()")
      time.sleep(2)
     




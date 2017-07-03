# eCat Static URI Register
This Python code creates static HTML and RDF (turtle) file indexes of items within a [Catalogue 
Service for the Web (CSW)](https://en.wikipedia.org/wiki/Catalog_Service_for_the_Web) service.

It is implemented by [Geoscience Australia](http://www.ga.gov.au) to allow a web spiders (think: Google Bot) to find 
links to, follow and then index the metadata of, items within the CSW catalogue. In GA's case, the catalogue targeted is 
[eCat Public](http://ecat.ga.gov.au/geonetwork/) which is implemented using the 
[GeoNetworks](http://geonetwork-opensource.org/) catalogue tool.

The static indexes that this code produces are online at:

* Datasets: <http://pid.geoscience.gov.au/dataset/>
* Web Services: <http://pid.geoscience.gov.au/service/>

The code only consists of a single Python file containing simple functions and a \__main\__ method used to perform the 
CSW requests, ID extraction and static file generation. The static files are layed out using Jinja2 templates within
the _templates_ directory.


## License
This code is licensed using Creative Commons 4.0 International (see [LICENSE file](LICENSE)).


## Authors & Contacts
This code repository is developed and maintained by [Geoscience Australia](http://www.ga.gov.au) (GA).

**Nicholas Car**  
Data Architect  
Geoscience Australia  
<nicholas.car@ga.gov.au>   
<http://orcid.org/0000-0002-8742-7730>  

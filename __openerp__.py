{
	'name' : 'OpenMRS Integration module',
	'version' : '0.1',
	'author' : 'Titus Kivite @ Intellisoft',
	'website' : 'http://www.intellisoftkenya.com/',
	'category' : 'Generic Modules/Others',
	'depends' : ['base','sale','account'],
	'description' : 'This module integrates openerp and openmrs',
	'demo_xml' : [],
	'data' : ['security/security.xml','openmrs_connector.xml', 'configuration.xml', 'order_views.xml', 'data/config_data.xml', 'security/ir.model.access.csv',],
	'active': False,
	'installable': True,
}




import os
from re import search
import requests
from bs4 import BeautifulSoup as soup
import ocr_sqm
import pandas as pd
import json


def search_zoopla_central_london(beds_max, beds_min, price_max, price_min ,expanded, radius = 5, pn =1):
  """Search for zoopla places in central london

  Args:
      beds_max: max beds
      beds_min: min beds
      price_max: price max

  Returns:
      Soup object of the page content
  """
  #                   https://www.zoopla.co.uk/for-sale/property/central-london/?beds_max=2&beds_min=3&price_max=650000&price_min=550000&view_type=list&q=Central%20London&radius=5&results_sort=newest_listings&search_source=home&pn=1
  #                   https://www.zoopla.co.uk/for-sale/property/central-london/?beds_max=3&beds_min=3&page_size=25&price_max=650000&price_min=550000&view_type=list&q=Central%20London&radius=5&results_sort=newest_listings&search_source=home&pn=1
  search_url =      f'https://www.zoopla.co.uk/for-sale/property/central-london/?{beds_max=}&{beds_min=}&{price_max=}&{price_min=}&view_type=list&q=Central%20London&results_sort=newest_listings&search_source=home&{pn=}'
  search_expanded = f'https://www.zoopla.co.uk/for-sale/property/central-london/?{beds_max=}&{beds_min=}&{price_max=}&{price_min=}&view_type=list&q=Central%20London&{radius=}&results_sort=newest_listings&search_source=home&{pn=}'
  if expanded:
    search_url = search_expanded
  print(search_url)
  page = requests.get(search_url)
  return soup(page.content, "html.parser")

def get_all_listings_one_page(bsobj):
  return bsobj.find_all('div', {'data-testid':'search-result'})

def get_all_links(sr):
  link_list = []
  for search_result in sr:
    link_object = search_result.find('a', {'data-testid':'listing-details-image-link'}, href=True)
    link_list.append(link_object['href'])
  return link_list

def get_all_listings_links_many_pages(beds_max,beds_min, price_max, price_min, expanded, radius, max_pages = 200):
  i = 1
  all_existing_links = []
  while True:
    page = search_zoopla_central_london(beds_max,beds_min,price_max,price_min, expanded, radius,i)
    sr = get_all_listings_one_page(page)
    links = get_all_links(sr)
    if len(links) == 0: break
    all_existing_links = all_existing_links + links
    i = i+1
    if i >= max_pages: break
  return all_existing_links


def get_information_from_listing(link, verbose = True):
  def get_property_info(name, label):
    try:
      info = property_page.find('span', {'data-testid':label}).text
      if verbose: print(f"{name}={info}")
      return info
    except:
      return None
  # find link to listing
  if verbose: print(f"https://www.zoopla.co.uk/{link}")
  listing_no = link.split('/')[3]
  # extract information from listing
  property_page = requests.get(url = f"https://www.zoopla.co.uk/{link}")
  property_page = soup(property_page.content, "html.parser")
  price = get_property_info('price', 'price')
  beds = get_property_info('beds', 'beds-label')
  area = get_property_info('area', 'floorarea-label')
  address = get_property_info('address', 'address-label')
  script_json = property_page.find('script',{'type':'application/ld+json'})
  site_json = json.loads(script_json.text)
  gmap = None
  for ele in site_json['@graph']:
    if ele['@type'] == 'Residence':
      gmap = ele['geo']

  next_data = json.loads(property_page.find('script', {'id':'__NEXT_DATA__'}).text)
  deets = next_data['props']['pageProps']['listingDetails']
  if deets['priceHistory'] is None:
    first_published = last_sale_new = last_sale_date = None
  else:
    if deets['priceHistory']['firstPublished'] is None:
      first_published = None
    else:
      first_published = deets['priceHistory']['firstPublished']['firstPublishedDate']
    # bad code smell...
    if deets['priceHistory']['lastSale'] is None:
      last_sale_date = None
      last_sale_new = None
    else:
      if 'date' in deets['priceHistory']['lastSale']: 
        last_sale_date = deets['priceHistory']['lastSale']['date']
      else:
        last_sale_date = None
      if 'newBuild' in deets['priceHistory']['lastSale']:
        last_sale_new = deets['priceHistory']['lastSale']['newBuild']
      else: 
        last_sale_new = None



  # find a floorplan and extract sqm from there
  floorplan = property_page.find('div', {'data-testid':'floorplan-thumbnail-0'})
  if floorplan is None:
    return_dict = {'address':address,'price':price, 'beds':beds, 'area':area, 'sqm':None, 'sqft': None, 'text':None, 'image':None,
    'link':f"https://www.zoopla.co.uk/{link}", 'listing_no':listing_no, 'gmap':gmap,
    'first_published':first_published,
    'last_sale_date':last_sale_date,
    'last_sale_new':last_sale_new,
    'deets':deets}
    with open(f'./json_data/{listing_no}.json', 'w', encoding='utf-8') as f:
      json.dump(return_dict, f, indent = 4)
    return return_dict
  # get all the links
  fp_links = []
  for image in floorplan.find_all('img'):
    fp_links.append(image['src'])
  # save the image with a random uuid (could probably use listing I guess...)
  img_data = requests.get(fp_links[0]).content
  path = f'./extracted_images/{listing_no}.jpg'
  with open(path, 'wb') as handler:
    handler.write(img_data)

  house1 = ocr_sqm.Property(path)
  house1.iterate_parameters()
  if verbose: print(house1)
  return_dict = {'address':address, 'price':price, 'beds':beds, 'area':area, 'sqm':house1.sqm, 'sqft': house1.sqft, 'text':house1.text, 'image':path, 
  'link':f"https://www.zoopla.co.uk/{link}", 'listing_no':listing_no,'gmap':gmap,
  'first_published':first_published,
  'last_sale_date':last_sale_date,
  'last_sale_new':last_sale_new,
  'deets':deets}
  
  with open(f'./json_data/{listing_no}.json', 'w', encoding='utf-8') as f:
    json.dump(return_dict, f, indent = 4)
  return return_dict

def filter_only_new_links(all_links):
  previous_data = os.listdir('json_data')
  previous_data = [x.split('.')[0] for x in previous_data]
  new_found_links = [x.split('/')[3] for x in all_links]
  return_links = []
  for i in range(len(new_found_links)):
    if (new_found_links[i] not in previous_data):
      return_links.append(all_links[i])
  return return_links

if __name__ == "__main__":
  beds_max = 3
  beds_min = 2
  price_max = 650000
  price_min = 550000
  # search_page = search_zoopla_central_london(beds_max,beds_min,price_max,price_min,True,5)
  # all_listings = get_all_listings_one_page(search_page)
  # all_links = get_all_links(all_listings)
  all_links = get_all_listings_links_many_pages(beds_max, beds_min, price_max, price_min, expanded = True, radius=5, max_pages=3)
  print(len(all_links))
  all_links = filter_only_new_links(all_links)
  print(len(all_links))

  if len(all_links)<1:
    print("No new property found!")
  else:
    detailed_info = []
    for link in all_links:
      detailed_info.append(get_information_from_listing(link, False))

    pd.DataFrame(detailed_info).to_csv('Properties.csv')

from re import search
import requests
from bs4 import BeautifulSoup as soup
import ocr_sqm
import pandas as pd


def search_zoopla_central_london(beds_max, beds_min, price_max, pn =1):
  """Search for zoopla places in central london

  Args:
      beds_max: max beds
      beds_min: min beds
      price_max: price max

  Returns:
      Soup object of the page content
  """
  search_url = f'https://www.zoopla.co.uk/for-sale/property/central-london/?{beds_max=}&{beds_min=}&{price_max=}&view_type=list&q=Central%20London&results_sort=newest_listings&search_source=home&{pn=}'
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

def get_all_listings_links_many_pages(beds_max,beds_min, price_max):
  i = 1
  all_existing_links = []
  while True:
    page = search_zoopla_central_london(beds_max,beds_min,price_max,i)
    sr = get_all_listings_one_page(page)
    links = get_all_links(sr)
    if len(links) == 0: break
    all_existing_links = all_existing_links + links
    i = i+1
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

  # find a floorplan and extract sqm from there
  floorplan = property_page.find('div', {'data-testid':'floorplan-thumbnail-0'})
  if floorplan is None:
    return {'price':price, 'beds':beds, 'area':area, 'sqm':None, 'sqft': None, 'image':None, 'link':f"https://www.zoopla.co.uk/{link}", 'listing_no':listing_no}
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
  return {'price':price, 'beds':beds, 'area':area, 'sqm':house1.sqm, 'sqft': house1.sqft, 'image':path, 'link':f"https://www.zoopla.co.uk/{link}", 'listing_no':listing_no}





if __name__ == "__main__":
  beds_max = 3
  beds_min = 3
  price_max = 750000
  #search_page = search_zoopla_central_london(beds_max,beds_min,price_max)
  #all_listings = get_all_listings_one_page(search_page)
  #all_links = get_all_links(all_listings)
  all_links = get_all_listings_links_many_pages(beds_max,beds_min,price_max)
  #print(all_links)
  print(len(all_links))

  detailed_info = []
  for link in all_links:
    detailed_info.append(get_information_from_listing(link, False))

  pd.DataFrame(detailed_info).to_csv('Properties.csv')

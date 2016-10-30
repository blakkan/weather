class WelcomeController < ApplicationController

  require 'nokogiri'

  def index

  end

  def display_forecast_query_screen


    uri =
      URI('http://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php')

    noaa_params = { 'listCitiesLevel' => '1'}

    uri.query = URI.encode_www_form(noaa_params)

    res = Net::HTTP.get_response(uri)

    doc = Nokogiri::XML(res.body)


    @raw_city_state_list = doc.xpath("//cityNameList").inner_text.split(/\|/)
    @lat_lon_list = doc.xpath("//latLonList").inner_text.split(" ")

    @city_state_lat_lon = @raw_city_state_list.zip(@lat_lon_list)


    @sorted_state_lat_lon = @city_state_lat_lon.sort{ |a, b| a[0].split(/,/)[0] <=> b[0].split(/,/)[0] }.
      sort{ |a, b| a[0].split(/,/)[1] <=> b[0].split(/,/)[1] }


  end

  def display_forecast_result

    #Get latitued and longitude
    uri =
      URI('http://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php')

    if params['button'] == 'by_zip_code'
      noaa_params = { 'listZipCodeList' => [params[:zip_code_field_name]]}
      uri.query = URI.encode_www_form(noaa_params)
      res = Net::HTTP.get_response(uri)

      doc = Nokogiri::XML(res.body)
      @lat_long = doc.xpath("//latLonList").inner_text



    elsif params['button'] == 'by_city_state'

      @lat_long = params[:city_state]

    else
      raise Exception::RuntimeError
    end

    #Now to the actual query
    uri =
      URI('http://graphical.weather.gov/xml/sample_products/browser_interface/ndfdBrowserClientByDay.php')
    noaa_params = {
      'lat' => @lat_long.split(/,/)[0].strip,
      'lon' => @lat_long.split(/,/)[1].strip,
      'numDays' => '7',
      'format' => '24 hourly'
    }
    uri.query = URI.encode_www_form(noaa_params)
    res = Net::HTTP.get_response(uri)
    doc = nil
    doc = Nokogiri::XML(res.body)

    @start_times = []
    doc.xpath("//data/time-layout[@summarization='24hourly']/layout-key[.='k-p24h-n7-1']/../start-valid-time").each { |d|
      @start_times << d.inner_text
    }

    @max_temps = []
    doc.xpath("//data/parameters/temperature[@type='maximum']/value").each { |d|
      @max_temps << d.inner_text
    }

    @min_temps = []
    doc.xpath("//data/parameters/temperature[@type='minimum']/value").each { |d|
      @min_temps << d.inner_text
    }

    @weather = []
    doc.xpath("//data/parameters/weather/weather-conditions/@weather-summary").each { |d|
      @weather << d.value
    }

    @table_data = [@start_times, @max_temps, @min_temps, @weather].transpose


  #  doc.xpath("/data/parameters/temperature[@type='maximum' and @time-layout='k-p24h-n7-1']/value").each { |d|
  #    p d.inner_text
  #  }

  #  doc.xpath("/data/parameters/temperature[@type='minimum' and @time-layout='k-p24h-n7-1']/value").each { |d|
  #    p d.inner_text
  #  }

  end

end

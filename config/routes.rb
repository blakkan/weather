Rails.application.routes.draw do

  root 'welcome#display_forecast_query_screen'

  get 'welcome/display_forecast_query_screen' => 'welcome#display_forecast_query_screen'
  get 'welcome/display_forecast_result' => 'welcome#display_forecast_result'

  # For details on the DSL available within this file, see http://guides.rubyonrails.org/routing.html
end

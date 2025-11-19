Rails.application.routes.draw do
  get "/home",     to: "pages#home"
  get "/scrapper", to: "pages#scrapper"
  get "/blogs",    to: "pages#blogs"
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  #to call 
  post "/make_call", to: "pages#make_call" 
  #to scrape linkdine profile
  post "/scrape_urls", to: "pages#scrape_urls"

  #to generate Blogs
  post "/generate_blog", to: "pages#generate_blog"
  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  # Defines the root path route ("/")
  root "pages#home"
end

from nba_api.stats.static import teams

teams_list = teams.get_teams()
print("teams_count:", len(teams_list))
print("first_team:", teams_list[0])

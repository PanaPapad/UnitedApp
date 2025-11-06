## This will be called after all any population of the KG
# THis will refresh the seasonStats of the teams (e.g. teamMatchesPlayed, teamWins, teamLosses, teamDraws)

from SPARQLWrapper import SPARQLWrapper, POST

GRAPHDB_ENDPOINT = "http://localhost:7200/repositories/UnitedApp/statements"  # adjust if remote

# Enrich match winner: add home,away win or draw based on the result
add_match_winner_query = """
  PREFIX : <http://semanticweb.org/unitedOntology#>
  INSERT {
  ?m :hasResult ?result .
  }
  WHERE {
    ?m a ?Match ;
      :matchHasTeamStats ?ts1 ;
      :matchHasTeamStats ?ts2 ;
      :hasHomeTeam ?t1 ;
      :hasAwayTeam ?t2.
    ?ts1 :statsOfTeam ?t1 ;
          :teamGoalsScored ?g1 .

    ?ts2 :statsOfTeam ?t2 ;
          :teamGoalsScored ?g2 .
  BIND(
      IF(?g1 = ?g2, :Draw,
        IF(?g1 > ?g2, :HomeWin, :AwayWin)
      ) AS ?result
    )
}
"""

# Team matches played: updates the matches played of a team
matches_played_query = """
PREFIX : <http://semanticweb.org/unitedOntology#>

DELETE {
    ?seasonStats :teamMatchesPlayed ?old_matches
}
INSERT {
    ?seasonStats :teamMatchesPlayed ?matches .
}
WHERE {
    # remove outdated values first
    OPTIONAL {
        ?team :teamHasSeasonStats ?seasonStats.
        ?seasonStats :teamMatchesPlayed ?old_matches
    } 
    ?team :teamHasSeasonStats ?seasonStats 
    {
    SELECT ?team (COUNT(?match) as ?matches)
    WHERE {
    	{
    	?match a :Match;
    		:hasHomeTeam ?team
		}
    	UNION{
    	?match a :Match;
    		:hasAwayTeam ?team
		}
	}GROUP BY(?team)
    }
}

"""

# Team wins, loses and draws query:
team_wins_loses_draws_query = """
PREFIX : <http://semanticweb.org/unitedOntology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

DELETE {
  ?seasonStats :teamWins ?oldwins .
  ?seasonStats :teamLoses ?oldloses .
  ?seasonStats :teamDraws ?olddraws .
}

INSERT {
  ?seasonStats :teamWins ?wins .
  ?seasonStats :teamLoses ?loses .
  ?seasonStats :teamDraws ?draws .

}
WHERE {
    # remove previous values first
    OPTIONAL {
        ?team :teamHasSeasonStats ?seasonStats.
        ?seasonStats :teamWins ?oldwins;
        			 :teamLoses ?oldloses;
        			 :teamDraws ?olddraws .
    } 
    ?team :teamHasSeasonStats ?seasonStats
    {
        SELECT ?team (COUNT(?match) as ?wins) (COUNT(?match2) as ?loses) (COUNT(?match3) as ?draws)
        WHERE {
          {
            ?match a :Match ;
                   :hasResult :HomeWin ;
                   :hasHomeTeam ?team .
          }
          UNION
          {
            ?match a :Match ;
                   :hasResult :AwayWin ;
                   :hasAwayTeam ?team .
          }
          UNION
          {
            ?match2 a :Match ;
                   :hasResult :HomeWin ;
                   :hasAwayTeam ?team .       
          }
           UNION
          {
           ?match2 a :Match ;
                   :hasResult :AwayWin ;
                   :hasHomeTeam ?team .
           }
            UNION
          {
            ?match3 a :Match ;
                   :hasResult :Draw ;
                   :hasAwayTeam ?team .       
          }
           UNION
          {
           ?match3 a :Match ;
                   :hasResult :Draw ;
                   :hasHomeTeam ?team .
           }
        } GROUP BY(?team)
	}
}

"""

# Team goals scored, and conceded query
team_goals_for_against_query = """
PREFIX : <http://semanticweb.org/unitedOntology#>

DELETE {
    ?seasonStats :teamGoalsFor ?oldgfor .
    ?seasonStats :teamGoalsAgainst ?oldgagainst .
}

INSERT {
    ?seasonStats :teamGoalsFor ?gfor .
    ?seasonStats :teamGoalsAgainst ?gagainst .
}
WHERE{
    # remove previous goals for and againts
    OPTIONAL{
        ?team :teamHasSeasonStats ?seasonStats.
        ?seasonStats :teamGoalsFor ?oldgfor;
        			:teamGoalsAgainst ?oldgagainst .
    }
    ?team :teamHasSeasonStats ?seasonStats
    {
    SELECT ?team (SUM(?gf) as ?gfor) (SUM(?ga) as ?gagainst)
    WHERE{
        ?ts :statsOfTeam ?team ;
            :teamGoalsScored ?gf    ;
          	:goalsConceded ?ga
       
        }GROUP BY(?team)
}
}

"""

# Team goal difference
team_goal_difference_query = """
    PREFIX : <http://semanticweb.org/unitedOntology#>
    DELETE{
        ?seasonStats :teamGoalDifference ?oldgd
    }
    INSERT{
        ?seasonStats :teamGoalDifference ?gd
    }
    WHERE {
        OPTIONAL{
            ?team :teamHasSeasonStats ?seasonStats.
        ?seasonStats :teamGoalDifference ?oldgd;
        }
        ?team :teamHasSeasonStats ?seasonStats.
        ?seasonStats :teamGoalsFor ?gf;
        :teamGoalsAgainst ?ga;
        BIND(?gf - ?ga as ?gd)    
}
"""

# Team Points
team_points_query = """
PREFIX : <http://semanticweb.org/unitedOntology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
DELETE {
  ?seasonStats :teamPoints ?old_points .  
}
INSERT {
  ?seasonStats :teamPoints ?points .
}
WHERE {
   OPTIONAL{
        ?team :teamHasSeasonStats ?seasonStats.
     	?seasonStats :teamPoints ?old_points;
    }    
  ?team a :Team ;
        :teamHasSeasonStats ?seasonStats .

  ?seasonStats :teamWins ?wins ;
                :teamDraws ?draws .
  # Formula: points = 3*wins + 1*draws
  BIND((3 * xsd:integer(?wins) + xsd:integer(?draws)) AS ?points)
}
"""

# Team clean sheets
team_clean_sheets_query = """
PREFIX : <http://semanticweb.org/unitedOntology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
DELETE {
  ?seasonStats :teamCleanSheets ?oldcleanSheets .
}
INSERT {
  ?seasonStats :teamCleanSheets ?cleanSheets .
}
WHERE {
    OPTIONAL{
        ?seasonStats :teamCleanSheets ?oldcleanSheets
    }    
  {
    SELECT ?team ?seasonStats (COALESCE(COUNT(?ms), 0) AS ?cleanSheets)
    WHERE {
      ?team a :Team ;
            :teamHasSeasonStats ?seasonStats .

      OPTIONAL {
        ?ms :statsOfTeam ?team ;
            :goalsConceded ?gc .
        FILTER(xsd:integer(?gc) = 0)
      }
    }
    GROUP BY ?team ?seasonStats
  }
}
"""

# Team yellow, red cards and offsides
team_yellow_red_cards_offsides_query = """
PREFIX : <http://semanticweb.org/unitedOntology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

DELETE {
  ?seasonStats :teamYellowCardsSeason ?oldyellowcards .
  ?seasonStats :teamRedCardsSeason ?oldredcards .
  ?seasonStats :teamOffsidesSeason ?oldoffsides 
    
}
INSERT {
  ?seasonStats :teamYellowCardsSeason ?yellowcards .
  ?seasonStats :teamRedCardsSeason ?redcards .
  ?seasonStats :teamOffsidesSeason ?offsides 
}
WHERE {
    OPTIONAL{
          ?seasonStats :teamYellowCardsSeason ?oldyellowcards .
  		  ?seasonStats :teamRedCardsSeason ?oldredcards .
          ?seasonStats :teamOffsidesSeason ?oldoffsides 
    }
  {
    SELECT ?team ?seasonStats (SUM(?yc) AS ?yellowcards) (SUM(?rc) AS ?redcards) (SUM(?of) AS ?offsides)
    WHERE {
      ?team a :Team ;
            :teamHasSeasonStats ?seasonStats .

      OPTIONAL {
        ?ms :statsOfTeam ?team ;
            :teamYellowCards ?yc .
      }
      OPTIONAL {
        ?ms :statsOfTeam ?team ;
            :teamRedCards ?rc .
      }
      OPTIONAL {
        ?ms :statsOfTeam ?team ;
            :teamOffsides ?of .
      }        
    }
    GROUP BY ?team ?seasonStats
  }
}
"""

all_queries = [add_match_winner_query, matches_played_query, team_wins_loses_draws_query, team_goals_for_against_query, team_goal_difference_query, team_clean_sheets_query, team_yellow_red_cards_offsides_query]
def refresh():
    """
    Function that runs all above queries that updated season stats
    """
    for query in all_queries:
        sparql = SPARQLWrapper(GRAPHDB_ENDPOINT)
        sparql.setMethod(POST)

        sparql.setQuery(query)
        sparql.query()

    print("Season stats refreshed successfully!")

if __name__ == "__main__":
    refresh()


from owlready2 import *

onto = get_ontology("http://semanticweb.org/unitedOntology")


with onto:

    # Entities
    class Human(Thing):
        label = "Human"
        comment = "A human being"
        pass
    
    class Player(Human):
        label = "Player"
        comment = "A perosn who plays for a team"
        pass

    class Team(Thing):
        label = "Team"
        comment = "A group of players that play together"
        pass

    class Coach(Human):
        label = "Coach"
        comment = "The coach of a team"
        pass

    class Match(Thing):
        label = "Match"
        comment = "A match between two teams"
        pass

    class Tournament(Thing):
        label = "Tournament"
        comment = "A tournament consisting of multiple matches. E.g., Premier League"
        pass

    class KnockOutTournament(Tournament):
        label = "KnockOutTournament"
        comment = "A tournament where teams are eliminated after a loss. E.g., FA Cup"
        pass

    class League(Tournament):
        label = "League"
        comment = "A tournament where teams play each other multiple times. E.g., Premier League"
        pass

    class Position(Thing):
        label = "Position"
        comment = "The position a player plays in. E.g., Forward, Midfielder, Defender, Goalkeeper"
        pass

    class Stadium(Thing):
        label = "Stadium"
        comment = "The stadium where a team plays their home matches"
        pass

    class Referee(Human):
        label = "Referee"
        comment = "The referee of a match"
        pass

    class Lineup(Thing):
        label = "Lineup"
        comment = "A team lineup in a specific match"
        pass

    # Properties
    class participatesInMatch(Team >> Match):
        label = "participatesInMatch"
        comment = "A team participates in a match"
        pass

    class matchHasTeam(Match >> Team):
        label = "matchHasTeam"
        comment = "A match has a team"
        inverse_property = participatesInMatch
        pass

    class matchPartOfTournament(Match >> Tournament, FunctionalProperty):
        label = "matchPartOfTournament"
        comment = "A match is part of a tournament"
        pass

    class tournamentHasMatch(Tournament >> Match):
        label = "tournamentHasMatch"
        comment = "A tournament has a match"
        inverse_property = matchPartOfTournament
        pass

    class playsFor(Player >> Team, FunctionalProperty):
        label = "playsFor"
        comment = "A player plays for a team"
        pass

    class hasPlayer(Team >> Player):
        label = "hasPlayer"
        comment = "A team has a player"
        inverse_property = playsFor
        pass

    class hasCoach(Team >> Coach, FunctionalProperty):
        label = "hasCoach"
        comment = "A team has a coach"
        pass

    class coachesTeam(Coach >> Team, FunctionalProperty):
        label = "coachesTeam"
        comment = "A coach coaches a team"
        inverse_property = hasCoach
        pass

    class playsInTournament(Team >> Tournament):
        label = "playsInTournament"
        comment = "A team plays in a tournament"
        pass

    class tournamentHasTeam(Tournament >> Team):
        label = "tournamentHasTeam"
        comment = "A tournament has a team"
        inverse_property = playsInTournament
        pass

    class hasPosition(Player >> Position):
        label = "hasPosition"
        comment = "A player has a position"
        pass

    class positionOfPlayer(Position >> Player):
        label = "positionOfPlayer"
        comment = "A position is played by a player"
        inverse_property = hasPosition
        pass

    class homeStadium(Team >> Stadium, FunctionalProperty):
        label = "homeStadium"
        comment = "A team has a home stadium"
        pass

    class stadiumOfTeam(Stadium >> Team, FunctionalProperty):
        label = "stadiumOfTeam"
        comment = "A stadium is the home of a team"
        inverse_property = homeStadium
        pass

    class hasCapacity(Stadium >> int, FunctionalProperty):
        label = "hasCapacity"
        comment = "The capacity of a stadium"
        pass

    class teamHasCode(Team >> str, FunctionalProperty):
        label = "teamHasCode"
        comment = "The code of the team, e.g MUN for Manchester United"
        pass

    # Human Data Properties
    class hasBirthDate(Human >> str, FunctionalProperty):
        label = "hasBirthDate"
        comment = "The birth date of a human"
        pass

    class hasNationality(Human >> str, FunctionalProperty):
        label = "hasNationality"
        comment = "The Nationality of a Human"
        pass

    class hasHeight(Human >> float, FunctionalProperty):
        label = "hasHeight"
        comment = "The height of a human in cm"
        pass

    # Previous Teams of a Player
    """
    Example:
    Player: Messi
    hasPreviousTeam:
        - PreviousTeamEntry:
            previousTeamName: Barcelona
            previousTeamStartDate: 2004-07-01
            previousTeamEndDate: 2021-08-05
        - PreviousTeamEntry:
            previousTeamName: PSG
            previousTeamStartDate: 2021-08-10
            previousTeamEndDate: 2023-06-30
    """
    class PreviousTeamEntry(Thing):
        label = "PreviousTeamEntry"
        comment = "Intermidate entity to represent a player's previous team and the duration"
        pass

    class hasPreviousTeam(Player >> PreviousTeamEntry):
        label = "hasPreviousTeam"
        comment = "A previous team entry of a player"
        pass

    class previousTeamName(PreviousTeamEntry >> Team, FunctionalProperty):
        label = "previousTeamName"
        comment = "The actual previous team"
        pass

    class previousTeamStartDate(PreviousTeamEntry >> str, FunctionalProperty):
        label = "previousTeamStartDate"
        comment = "The start date of the player's tenure at the previous team"
        pass

    class previousTeamEndDate(PreviousTeamEntry >> str, FunctionalProperty):
        label = "previousTeamEndDate"
        comment = "The end date of the player's tenure at the previous team"
        pass

    # Awards
    class Award(Thing):
        label = "Award"
        comment = "An award"
        pass
    
    class awardName(Award >> str, FunctionalProperty):
        label = "awardName"
        comment = "The name of the award"
        pass

    class awardYear(Award >> int, FunctionalProperty):
        label = "awardYear"
        comment = "The year the award was given"
        pass

    # Player Awards
    class PlayerAward(Award):
        label = "PlayerAward"
        comment = "An award given to a player"
        pass

    class awardGivenToPlayer(PlayerAward >> Player):
        label = "awardGivenToPlayer"
        comment = "The player who received the award"
        pass

    class playerReceivedAward(Player >> PlayerAward):
        label = "playerReceivedAward"
        comment = "The awards received by a player"
        inverse_property = awardGivenToPlayer
        pass

    # Team Awards
    class TeamAward(Award):
        label = "TeamAward"
        comment = "An award given to a team"
        pass

    class awardGivenToTeam(TeamAward >> Team):
        label = "awardGivenToTeam"
        comment = "The team who received the award"
        pass

    class teamReceivedAward(Team >> TeamAward):
        label = "teamReceivedAward"
        comment = "The awards received by a team"
        inverse_property = awardGivenToTeam
        pass
    
    # Lineup Properties
    class lineupOfMatch(Lineup >> Match, FunctionalProperty):
        label = "lineupOfMatch"
        comment = "The match the lineup belongs to"
        pass

    class lineupOfTeam(Lineup >> Team, FunctionalProperty):
        label = "lineupOfTeam"
        comment = "The team the lineup belongs to (of a specific match)"
        pass

    class teamHasLineup(Team >> Lineup):
        label = "teamHasLineup"
        comment = "A team has a lineup (of a specific match)"
        inverse_property = lineupOfTeam
        pass

    class PlayerInLineup(Thing):
        label = "PlayerInLineup"
        comment = "Intermidate entity to represent a player in a lineup with additional properties"
        pass

    class hasPlayerInLineup(Lineup >> PlayerInLineup):
        label = "hasPlayerInLineup"
        comment = "A player in the lineup"
        pass
    
    class lineupHasPlayer(PlayerInLineup >> Player):
        label = "lineupHasPlayer"
        comment = "The actual player in the lineup"
        pass

    class playerPositionInLineup(PlayerInLineup >> Position, FunctionalProperty):
        label = "playerPositionInLineup"
        comment = "The position a player plays in a specific lineup"
        pass

    class lineUpHasCaptain(Lineup >> PlayerInLineup, FunctionalProperty):
        label = "lineUpHasCaptain"
        comment = "The captain in a specific lineup"
        pass

    class captainOfLineup(PlayerInLineup >> Lineup, FunctionalProperty):
        label = "captainOfLineup"
        comment = "The lineup where the player is the captain"
        inverse_property = lineUpHasCaptain
        pass

    class isStartingPlayerInLineup(PlayerInLineup >> bool, FunctionalProperty):
        label = "isStartingPlayerInLineup"
        comment = "If the player is a starting player in a specific lineup"
        pass

    class playerShirtNumberInLineup(PlayerInLineup >> int, FunctionalProperty):
        label = "playerShirtNumberInLineup"
        comment = "The shirt number of a player in a specific lineup"
        pass

    class formationOfLineup(Lineup >> str, FunctionalProperty):
        label = "formationOfLineup"
        comment = "The formation of a specific lineup. E.g., 4-3-3"
        pass

    # instances of Position
    # Goalkeeper
    GK = Position("GK")
    
    # Defenders
    LB = Position("LB")
    LWB = Position("LWB")
    CB = Position("CB")
    RB = Position("RB")
    RWB = Position("RWB")
    
    # Midfielders
    DM = Position("DM")
    CDM = Position("CDM")
    CM = Position("CM")
    CAM = Position("CAM")
    LM = Position("LM")
    RM = Position("RM")
    AM = Position("AM")
    
    # Forwards
    LW = Position("LW")
    RW = Position("RW")
    ST = Position("ST")
    CF = Position("CF")

    
    # Match Properties
    class MatchResult(Thing): 
        label = "MatchResult"
        comment = "The result of a match"
        pass

    # instances of MatchResult
    HomeWin = MatchResult("HomeWin")
    AwayWin = MatchResult("AwayWin")
    Draw = MatchResult("Draw")

    class hasResult(Match >> MatchResult, FunctionalProperty):
        label = "hasResult"
        comment = "The result of the match"
        pass

    class resultOfMatch(MatchResult >> Match):
        label = "resultOfMatch"
        comment = "The match the result belongs to"
        inverse_property = hasResult
        pass

    class hasHomeTeam(Match >> Team):
        label = "hasHomeTeam"
        comment = "A match has a home team"
        pass

    class hasAwayTeam(Match >> Team):
        label = "hasAwayTeam"
        comment = "A match has an away team"
        pass

    class hasReferee(Match >> Referee):
        label = "hasReferee"
        comment = "A match has a referee"
        pass

    class referryOfMatch(Referee >> Match):
        label = "referryOfMatch"
        comment = "A referee officiates a match"
        inverse_property = hasReferee
        pass

    class matchDate(Match >> str):
        label = "matchDate"
        comment = "The date of the match"
        pass

    class matchHasStadium(Match >> Stadium):
        label = "matchHasStadium"
        comment = "The location of the match"
        pass

    class stadiumOfMatch(Stadium >> Match):
        label = "stadiumOfMatch"
        comment = "A stadium hosts a match"
        inverse_property = matchHasStadium
        pass


    # Team Match Stats Properties
    class TeamMatchStats(Thing):
        label = "TeamMatchStats"
        comment = "Statistics of a team in a match"
        pass

    class matchHasTeamStats(Match >> TeamMatchStats):
        label = "matchHasTeamStats"
        comment = "A match has match statistics"
        pass
    
    class teamStatsOfMatch(TeamMatchStats >> Match, FunctionalProperty):
        label = "teamStatsOfMatch"
        comment = "The match the statistics belong to"
        inverse_property = matchHasTeamStats
        pass

    class statsOfTeam(TeamMatchStats >> Team, FunctionalProperty):
        label = "statsOfTeam"
        comment = "The team the statistics belong to"
        pass

    class teamGoalsScored(TeamMatchStats >> int, FunctionalProperty):
        label = "teamGoalsScored"
        comment = "The number of goals scored by the team in a match"
        pass

    class goalsConceded(TeamMatchStats >> int, FunctionalProperty):
        label = "goalsConceded"
        comment = "The number of goals conceded by the team in a match"
        pass

    class ballPossession(TeamMatchStats >> float, FunctionalProperty):
        label = "ballPossession"
        comment = "The ball possession percentage of a team in a match"
        pass

    class corners(TeamMatchStats >> int, FunctionalProperty):
        label = "corners"
        comment = "The number of corners taken by a team in a match"
        pass

    class teamShotsOnTarget(TeamMatchStats >> int, FunctionalProperty):
        label = "teamShotsOnTarget"
        comment = "The number of shots on target by a team in a match"
        pass

    class teamTotalShots(TeamMatchStats >> int, FunctionalProperty):
        label = "teamTotalShots"
        comment = "The total number of shots by a team in a match"
        pass

    class teamFoulsCommitted(TeamMatchStats >> int, FunctionalProperty):
        label = "teamFoulsCommitted"
        comment = "The number of fouls committed by a team in a match"
        pass

    class teamYellowCards(TeamMatchStats >> int, FunctionalProperty):
        label = "teamYellowCards"
        comment = "The number of yellow cards received by a team in a match"
        pass

    class teamRedCards(TeamMatchStats >> int, FunctionalProperty):
        label = "teamRedCards"
        comment = "The number of red cards received by a team in a match"
        pass
  
    class teamOffsides(TeamMatchStats >> int, FunctionalProperty):
        label = "teamOffsides"
        comment = "The number of offsides by a team in a match"
        pass

    # Player Stats in a Match
    class PlayerMatchStats(Thing):
        label = "PlayerMatchStats"
        comment = "Statistics of a player in a match"
        pass

    class matchHasPlayerStats(Match >> PlayerMatchStats):
        label = "matchHasPlayerStats"
        comment = "A match has player statistics"
        pass

    class playerStatsOfMatch(PlayerMatchStats >> Match, FunctionalProperty):
        label = "playerStatsOfMatch"
        comment = "The match the statistics belong to"
        inverse_property = matchHasPlayerStats
        pass

    class matchStatsOfPlayer(PlayerMatchStats >> Player, FunctionalProperty):
        label = "matchStatsOfPlayer"
        comment = "The player the statistics belong to"
        pass

    class playerHasMatchStats(Player >> PlayerMatchStats):
        label = "playerHasMatchStats"
        comment = "A player has match statistics"
        inverse_property = matchStatsOfPlayer
        pass

    class minutesPlayed(PlayerMatchStats >> int, FunctionalProperty):
        label = "minutesPlayed"
        comment = "The number of minutes played by a player in a match"
        pass

    class playerGoalsScored(PlayerMatchStats >> int, FunctionalProperty):
        label = "playerGoalsScored"
        comment = "The number of goals scored by a player in a match"
        pass

    class assists(PlayerMatchStats >> int, FunctionalProperty):
        label = "assists"
        comment = "The number of assists by a player in a match"
        pass

    class playerShotsOnTarget(PlayerMatchStats >> int, FunctionalProperty):
        label = "playerShotsOnTarget"
        comment = "The number of shots on target by a player in a match"
        pass

    class playerTotalShots(PlayerMatchStats >> int, FunctionalProperty):
        label = "playerTotalShots"
        comment = "The total number of shots by a player in a match"
        pass

    class playerPassesCompleted(PlayerMatchStats >> int, FunctionalProperty):
        label = "playerPassesCompleted"
        comment = "The number of passes completed by a player in a match"
        pass

    class playerFoulsCommitted(PlayerMatchStats >> int, FunctionalProperty):
        label = "playerFoulsCommitted"
        comment = "The number of fouls committed by a player in a match"
        pass

    class playerYellowCards(PlayerMatchStats >> int, FunctionalProperty):
        label = "playerYellowCards"
        comment = "The number of yellow cards received by a player in a match"
        pass

    class playerRedCard(PlayerMatchStats >> bool, FunctionalProperty):
        label = "playerRedCards"
        comment = "If a player received a red card in a match"
        pass

    class playerOffsides(PlayerMatchStats >> int, FunctionalProperty):
        label = "playerOffsides"
        comment = "The number of offsides by a player in a match"
        pass

    # Season Stats
    class TeamSeasonStats(Thing):
        label = "SeasonStats"
        comment = "Statistics of a team in a season of a tournament"
        pass

    class seasonStatsOfTeam(TeamSeasonStats >> Team, FunctionalProperty):
        label = "seasonStatsOfTeam"
        comment = "The team the season statistics belong to"
        pass

    class teamHasSeasonStats(Team >> TeamSeasonStats):
        label = "teamHasSeasonStats"
        comment = "A team has season statistics"
        inverse_property = seasonStatsOfTeam
        pass

    class teamSeasonStatsOfTournament(TeamSeasonStats >> Tournament, FunctionalProperty):
        label = "teamSeasonStatsOfTournament"
        comment = "The tournament the season statistics belong to"
        pass

    class teamMatchesPlayed(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamMatchesPlayed"
        comment = "The number of matches played by a team in a season"
        pass

    class teamWins(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamWins"
        comment = "The number of wins by a team in a season"
        pass

    class teamDraws(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamDraws"
        comment = "The number of draws by a team in a season"
        pass    

    class teamLosses(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamLosses"
        comment = "The number of losses by a team in a season"
        pass

    class teamGoalsFor(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamGoalsFor"
        comment = "The number of goals scored by a team in a season"
        pass

    class teamGoalsAgainst(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamGoalsAgainst"
        comment = "The number of goals conceded by a team in a season"
        pass

    class teamGoalDifference(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamGoalDifference"
        comment = "The goal difference of a team in a season"
        pass

    class teamPoints(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamPoints"
        comment = "The number of points of a team in a season"
        pass

    class teamCleanSheets(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamCleanSheets"
        comment = "The number of clean sheets by a team in a season"
        pass

    class teamYellowCardsSeason(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamYellowCardsSeason"
        comment = "The number of yellow cards received by a team in a season"
        pass

    class teamRedCardsSeason(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamRedCardsSeason"
        comment = "The number of red cards received by a team in a season"
        pass

    class teamOffsidesSeason(TeamSeasonStats >> int, FunctionalProperty):
        label = "teamOffsidesSeason"
        comment = "The number of offsides by a team in a season"
        pass

    class PlayerSeasonStats(Thing):
        label = "PlayerSeasonStats"
        comment = "Statistics of a player in a season of a tournament"
        pass

    class seasonStatsOfPlayer(PlayerSeasonStats >> Player, FunctionalProperty):
        label = "seasonStatsOfPlayer"
        comment = "The player the season statistics belong to"
        pass

    class playerHasSeasonStats(Player >> PlayerSeasonStats):
        label = "playerHasSeasonStats"
        comment = "A player has season statistics"
        inverse_property = seasonStatsOfPlayer
        pass

    class playerSeasonStatsOfTournament(PlayerSeasonStats >> Tournament, FunctionalProperty):
        label = "playerSeasonStatsOfTournament"
        comment = "The tournament the season statistics belong to"
        pass

    class playerMatchesPlayed(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerMatchesPlayed"
        comment = "The number of matches played by a player in a season"
        pass

    class playerMinutesPlayedSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerMinutesPlayedSeason"
        comment = "The number of minutes played by a player in a season"
        pass

    class playerGoalsScoredSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerGoalsScoredSeason"
        comment = "The number of goals scored by a player in a season"
        pass

    class playerAssistsSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerAssistsSeason"
        comment = "The number of assists by a player in a season"
        pass

    class playerShotsOnTargetSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerShotsOnTargetSeason"
        comment = "The number of shots on target by a player in a season"
        pass

    class playerTotalShotsSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerTotalShotsSeason"
        comment = "The total number of shots by a player in a season"
        pass

    class playerPassesCompletedSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerPassesCompletedSeason"
        comment = "The number of passes completed by a player in a season"
        pass

    class playerFoulsCommittedSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerFoulsCommittedSeason"
        comment = "The number of fouls committed by a player in a season"
        pass

    class playerYellowCardsSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerYellowCardsSeason"
        comment = "The number of yellow cards received by a player in a season"
        pass

    class playerRedCardsSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerRedCardsSeason"
        comment = "The number of red cards received by a player in a season"
        pass

    class playerOffsidesSeason(PlayerSeasonStats >> int, FunctionalProperty):
        label = "playerOffsidesSeason"
        comment = "The number of offsides by a player in a season"
        pass



# Save the ontology to a file
onto.save(file = "unitedOntology.owl", format = "rdfxml")


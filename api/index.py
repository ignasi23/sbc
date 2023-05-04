from flask import Flask, render_template, request, jsonify
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import os


app = Flask(__name__, template_folder=os.path.abspath("templates"))

def get_player_info(name):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT ?player ?playerLabel ?wikidataId ?height
        WHERE {{
            ?player rdf:type dbo:SoccerPlayer.
            ?player rdfs:label ?playerLabel.
            ?player owl:sameAs ?wikidataId.
            OPTIONAL {{ ?player dbo:height ?height }}.
            FILTER (regex(?playerLabel, "{name}", "i") && strstarts(str(?wikidataId), "http://www.wikidata.org/entity/")).
        }}
        LIMIT 1
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    if results["results"]["bindings"]:
        return results["results"]["bindings"][0]
    else:
        return None

def get_player_teams(wikidata_id):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?team ?teamLabel
        WHERE {{
            wd:{wikidata_id} wdt:P31 wd:Q5;
                               wdt:P106 wd:Q937857;
                               wdt:P54 ?team.
            ?team rdfs:label ?teamLabel.
            FILTER (lang(?teamLabel) = "en")
        }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    if results["results"]["bindings"]:
        return [binding for binding in results["results"]["bindings"]]
    else:
        return None

def get_player_positions(wikidata_id):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?position ?positionLabel
        WHERE {{
            wd:{wikidata_id} wdt:P31 wd:Q5;
                               wdt:P106 wd:Q937857;
                               wdt:P413 ?position.
            ?position rdfs:label ?positionLabel.
            FILTER (lang(?positionLabel) = "en")
        }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    if results["results"]["bindings"]:
        return [binding for binding in results["results"]["bindings"]]
    else:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        player_name = request.form["player_name"]
        player_info = get_player_info(player_name)

        if player_info:
            wikidata_id = player_info["wikidataId"]["value"].split("/")[-1]
            teams = get_player_teams(wikidata_id)
            positions = get_player_positions(wikidata_id)
            return render_template("results.html", player_info=player_info, wikidata_id=wikidata_id, teams=teams, positions=positions)
        else:
            return render_template("index.html", error=f"No se ha encontrado un jugador con el nombre: '{player_name}'.")
    return render_template("index.html")

@app.route("/search_players", methods=["GET"])
def search_players():
    term = request.args.get("term")
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT ?player ?playerLabel
        WHERE {{
            ?player rdf:type dbo:SoccerPlayer.
            ?player rdfs:label ?playerLabel.
            FILTER (regex(?playerLabel, "{term}", "i")).
        }}
        LIMIT 10
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    if results["results"]["bindings"]:
        player_names = [result["playerLabel"]["value"] for result in results["results"]["bindings"]]
        return jsonify(player_names)
    else:
        return jsonify([])

if __name__ == "__main__":
    app.run(debug=True)

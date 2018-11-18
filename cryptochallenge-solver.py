#!/usr/bin/python
import shutil

import requests, json, os
import re

from jinja2 import BaseLoader, TemplateNotFound, Environment, FileSystemLoader
from os.path import join, exists, getmtime

class Scraper:
    def __init__( self ):
        self.client = requests.Session()

    def get_payload( self ):
        fetch_results = self.client.get( url="https://cryptochallenge.io/cryptochallenge.asp" )
        return self.Parser.scrape( "payload", str( fetch_results.content, encoding="utf-8" ) )

    def get_best_match( self, cipher ):
        # POST https://6n9n93nlr5.execute-api.us-east-1.amazonaws.com/prod/dict
        # H Content-type: application/x-www-form-urlencoded"
        # H Origin: https://quipqiup.com"
        # H Referer: https://quipqiup.com/
        # BODY
        # '{"ciphertext":"HWYYB RV MSO RQMOYOVM IFRG UB MSWVO HSW UWYYWH MYWTUJO. - EOWYEO HFVSRQEMWQ","clues":"","shards":7,"shardidx":6,"time":7}'
        # note:  need to iterate through shardidx, 0-#shards

        self.client.headers.update(
            {
                'Accept-Encoding': "gzip, deflate, br",
                'Referer': "https://quipqiup.com/",
                'Content-type': "application/x-www-form-urlencoded",
                'Origin': "https://quipqiup.com/"
            }
        )

        results = list()

        num_shards = 7
        for shard in range( num_shards ):
            body = {
                "ciphertext": cipher,
                "clues": "",
                "shards": num_shards,
                "shardidx": shard,
                "time": 7
            }

            # print( "Shard {}".format( shard ) )
            these_results = self.client.post( "https://6n9n93nlr5.execute-api.us-east-1.amazonaws.com/prod/dict", json.dumps( body ) ).content
            results.append(these_results)

        solutions = list()
        for result in results:
            obj = json.loads(result)
            solutions.append( obj )

        bests = list()
        for solution in solutions:
            bests.append( sorted(solution["solutions"], key=lambda k: k['logp'], reverse=True)[0] )

        return sorted( bests, key=lambda k: k['logp'], reverse=True )[0]["plaintext"]


    class Parser:
        @staticmethod
        def scrape( datapoint, text ):
            cases = {
                "payload": Scraper.Parser.payload
            }
            return cases[ datapoint ]( text )

        @staticmethod
        def payload( text ):
            varline = ""

            for line in text.split("\n"):
                if "var p = " in line:
                    varline = line.strip()

            return varline.replace("var p = '", "").replace("';", "")



def Main():
    myScraper = Scraper()

    cipher_value = myScraper.get_payload()

    cipher_answer = myScraper.get_best_match( cipher_value )

    env = Environment( loader=FileSystemLoader("template" ) )

    template = env.get_template("index.html")
    output_from_parsed_template = template.render(cipher=cipher_value, answer=cipher_answer)

    with open("output/index.html", "w") as fh:
        fh.write(output_from_parsed_template)

if __name__=="__main__":
    Main()
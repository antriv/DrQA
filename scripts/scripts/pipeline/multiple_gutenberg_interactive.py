import torch
import argparse
import code
import prettytable
import logging

import csv
import sys
import vobject
import urllib.request as ur

from drqa import pipeline
from drqa.retriever import utils

logger = logging.getLogger()
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s: [ %(message)s ]', '%m/%d/%Y %I:%M:%S %p')
console = logging.StreamHandler()
console.setFormatter(fmt)
logger.addHandler(console)

from gutenberg.query import get_etexts
from gutenberg.query import get_metadata

parser = argparse.ArgumentParser()
parser.add_argument('--reader-model', type=str, default=None,
                    help='Path to trained Document Reader model')
parser.add_argument('--retriever-model', type=str, default=None,
                    help='Path to Document Retriever model (tfidf)')
parser.add_argument('--doc-db', type=str, default=None,
                    help='Path to Document DB')
parser.add_argument('--tokenizer', type=str, default=None,
                    help=("String option specifying tokenizer type to "
                          "use (e.g. 'corenlp')"))
parser.add_argument('--candidate-file', type=str, default=None,
                    help=("List of candidates to restrict predictions to, "
                          "one candidate per line"))
parser.add_argument('--no-cuda', action='store_true',
                    help="Use CPU only")
parser.add_argument('--gpu', type=int, default=-1,
                    help="Specify GPU device id to use")
args = parser.parse_args()

args.cuda = not args.no_cuda and torch.cuda.is_available()
if args.cuda:
    torch.cuda.set_device(args.gpu)
    logger.info('CUDA enabled (GPU %d)' % args.gpu)
else:
    logger.info('Running on CPU only.')

if args.candidate_file:
    logger.info('Loading candidates from %s' % args.candidate_file)
    candidates = set()
    with open(args.candidate_file) as f:
        for line in f:
            line = utils.normalize(line.strip()).lower()
            candidates.add(line)
    logger.info('Loaded %d candidates.' % len(candidates))
else:
    candidates = None

logger.info('Initializing pipeline...')
DrQA = pipeline.DrQA(
    cuda=args.cuda,
    fixed_candidates=candidates,
    reader_model=args.reader_model,
    ranker_config={'options': {'tfidf_path': args.retriever_model}},
    db_config={'options': {'db_path': args.doc_db}},
    tokenizer=args.tokenizer
)


# ------------------------------------------------------------------------------
# Drop in to interactive mode
# ------------------------------------------------------------------------------
def convert(file):
    reader = csv.reader(open(file, 'rb'))

    for row in reader:
        print('BEGIN VCARD')
        print('Rank:' + row[0])
        print('Answer:' + row[1])
        print('Doc-ID' + row[2])
        print('Doc-Title' + row[3])
        print('Doc-Author' + row[4])
        print('Doc-Link' + row[5])
        print('END VCARD')

def process(question, candidates=None, top_n=3, n_docs=3):
    torch.cuda.empty_cache()
    title = ''
    author = ''
    predictions = DrQA.process(
        question, candidates, top_n, n_docs, return_context=True
    )

    table = prettytable.PrettyTable(
        ['Rank', 'Answer', 'Doc-ID', 'Doc-Title', 'Doc-Author', 'Doc-Link']
    )
    for i, p in enumerate(predictions):      
        if not list(get_metadata('title', p['doc_id'])):
            title = 'Not Available'
        else:
            tittle = list(get_metadata('title', p['doc_id']))[0]

        if not list(get_metadata('author', p['doc_id'])):
            author = 'Not Available'
        else:
            author = list(get_metadata('author', p['doc_id']))[0]
       
        if not list(get_metadata('formaturi', p['doc_id'])):
            url = 'Not Available'
        else:
            url = list(get_metadata('formaturi', p['doc_id']))[0]

        table.add_row([i+1, p['span'], p['doc_id'], tittle, author, url])
    print('Top Predictions:')
    print(table)

    with open('/data/MRC_Google_Compete/DrQA/result/output.csv','w') as f:
        writer = csv.writer(f)
        writer.writerow(['Rank', 'Answer', 'Doc-ID', 'Doc-Title', 'Doc-Author', 'Doc-Link'])
        for i, p in enumerate(predictions):      
            if not list(get_metadata('title', p['doc_id'])):
                title = 'Not Available'
            else:
                tittle = list(get_metadata('title', p['doc_id']))[0]
            if not list(get_metadata('author', p['doc_id'])):
                author = 'Not Available'
            else:
                author = list(get_metadata('author', p['doc_id']))[0]    
            if not list(get_metadata('formaturi', p['doc_id'])):
                url = 'Not Available'
            else:
                url = list(get_metadata('formaturi', p['doc_id']))[0]
            writer.writerow([str(i+1), str(p['span']), str(p['doc_id']), tittle, author, url])
    
    photo_url = "http://www.abcrealestate.co.za/resize/100/150/uploads/agents/2012/03/testagent.jpg"
    f = ur.urlopen(photo_url)
    image_data = f.read()
    f.close()
   
    with open('/data/MRC_Google_Compete/DrQA/result/output.csv', 'r' ) as source:
        has_header = csv.Sniffer().has_header(source.read(1024))
        source.seek(0)  # Rewind.
        reader = csv.reader(source)
        if has_header:
            next(reader)
            #reader = csv.reader(source)
            for row in reader:
                vcf = open("/data/MRC_Google_Compete/DrQA/result/vcf/"+ row[0] + ".vcf", 'w')
                vcf.write('Rank: ' + row[0] + "\n")
                vcf.write('Answer: ' + row[1] + "\n")
                vcf.write('Doc-ID: ' + row[2] + "\n")
                vcf.write('Doc-Title: ' + row[3] + "\n")
                vcf.write('Doc-Author: ' + row[4] + "\n")
                vcf.write('Doc-Link: ' + row[5]+ "\n")
                #vcf.write(image_data)
                vcf.write( "\n")
                vcf.close()

'''
response = HttpResponse(mimetype='text/x-vcard')
response['Content-Disposition'] = 'attachment; filename="%s.vcf"' % agent.get_full_name()
response.write(card.serialize())
return response
'''
           

banner = """
Interactive MRC
>> process(question, candidates=None, top_n=3, n_docs=3)
>> usage()
"""


def usage():
    print(banner)


code.interact(banner=banner, local=locals())

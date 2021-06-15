from os.path import join
from Bio import SeqIO
import subprocess
import re
from pipeline import *


def fetchingSequences():
    subprocess.run("./fetch_data.sh")

def changeNameSequences():
    sequences_file = open("output/reference/sequences.fasta", "r")
    list_of_lines = sequences_file.readlines()
    for index in range(len(list_of_lines)):
        if list_of_lines[index].startswith(">"):
            splitted_line = list_of_lines[index].split("/")
            name = ">" + splitted_line[2] + "\n"
            list_of_lines[index] = name

    sequences_file = open("output/sequences.fasta", "w")
    sequences_file.writelines(list_of_lines)
    sequences_file.close()

def getGene(gene, pattern):
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    s = pattern
    directory_name = gene + "_gene"
    file_name = gene + "_gene.fasta"
    path =  os.path.join("output", directory_name, file_name)
    new_file = open(path, "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


def getORF1abGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    s = 'ATGGAGAGCC(.*)TAACAACTAA'
    new_file = open("output/ORF1ab_gene/ORF1abGene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")
    
    new_file.close()


def getSGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    s = 'ATGTTTGTTT(.*)TTACACATAA'
    new_file = open("output/S_gene/S.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


def getORF3aGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    s = 'ATGGATTTGT(.*)GCCTTTGTAA'
    new_file = open("output/ORF3b_gene/ORF3b_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


def getORF3bGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    s = 'ATGAGGCTTT(.*)GCCTTTGTAA'
    new_file = open("output/ORF3b_gene/ORF3b_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


def getEGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    s = 'ATGTACTCAT(.*)TCTGGTCTAA'
    new_file = open("output/E_gene/E_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


def getMGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    s = 'ATG[GT]CAGATT(.*)TGTACAGTAA' #ici, presence de mutation dans les 10 premieres bases, d'ou la necessite de mettre des inconnus
    new_file = open("output/M_gene/M_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


def getORF6Gene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    # ici, presence de mutation dans les 10 premieres bases, d'ou la necessite de mettre des inconnus
    s = 'ATGTTTCATC(.*)GATTGA[CT]TAA'
    new_file = open("output/ORF6_gene/ORF6_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()

def getORF7aGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    # ici, presence de mutation dans les 10 premieres bases, d'ou la necessite de mettre des inconnus
    s = 'ATGAAAATTAT(.*)GACAGAATGA'
    new_file = open("output/ORF7a_gene/ORF7a_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()

def getORF6Gene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    # ici, presence de mutation dans les 10 premieres bases, d'ou la necessite de mettre des inconnus
    s = 'ATGTTTCATC(.*)GATTGA[CT]TAA'
    new_file = open("output/ORF6_gene/ORF6_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()

def getORF7aGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    # ici, presence de mutation dans les 10 premieres bases, d'ou la necessite de mettre des inconnus
    s = 'ATGAAAATTAT(.*)GACAGAATGA'
    new_file = open("output/ORF7a_gene/ORF7a_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


def getORF7bGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    # ici, presence de mutation dans les 10 premieres bases, d'ou la necessite de mettre des inconnus
    s = 'ATGATTGAACTTTCATTAATTGACTTCTATTTGTGCTTTTTAGCCTTTCTGCTATTCCTTGTTTTAATTATGCTTATTATCTTTTGGTTCTCACTTGAACTGCAAGATCATAATGAAACTTGTCACGCCTAA'
    new_file = open("output/ORF7b_gene/ORF7b_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()

def getORF8Gene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    # ici, presence de mutation dans les 10 premieres bases, d'ou la necessite de mettre des inconnus
    s = 'ATGAAATTTCTTGTTTT(.*)TTT[TC]ATCTAA'
    new_file = open("output/ORF8_gene/ORF8_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


def getNGene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    # ici, presence de mutation dans les 10 premieres bases, d'ou la necessite de mettre des inconnus
    s = 'ATGTCT[CG][AT][TA]AAT(.*)TCAGGCCTAA'
    new_file = open("output/N_gene/N_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


def getORF10Gene():
    sequences_file = open("output/reference/sequences.fasta", "r").read()
    list_of_sequences = sequences_file.split(">")
    # ici, presence de mutation dans les 10 premieres bases, d'ou la necessite de mettre des inconnus
    s = 'ATGGGCTATA(.*)TCTCACATAG'
    new_file = open("output/ORF10_gene/ORF10_gene.fasta", "w")
    for index in range(len(list_of_sequences)):
        if list_of_sequences[index] == "":
            continue
        name = list_of_sequences[index].split("\n")[0]
        gene_sequence = list_of_sequences[index].replace("\n", "")
        gene_sequence = (re.search(s, gene_sequence).group())
        new_file.writelines(">" + name + "\n")
        new_file.writelines(gene_sequence + "\n")

    new_file.close()


if __name__ == '__main__':
#    fetchingSequences()
#    changeNameSequences()
    getGene('ORF1ab', 'ATGGAGAGCC(.*)TAACAACTAA')
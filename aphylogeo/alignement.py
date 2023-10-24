import sys
import os
import subprocess
import glob
import Bio.SeqIO
import statistics as st
# import pymuscle5
from itertools import combinations
from collections import defaultdict
from Bio.Align.Applications import ClustalwCommandline
from Bio.Align.Applications import MafftCommandline
from io import StringIO
from Bio import pairwise2
from Bio.Seq import Seq
from Bio import AlignIO
from .multiProcessor import Multi
from pathlib import Path


class AlignSequences:
    """
    Class that perform a heuristic Multiple Sequence Alignement and windi from a single fasta file.
    """

    def __init__(self, sequences, window_size, step_size, makeDebugFiles, bootstrapAmount, alignment_method, reference_gene_file, fit_method):
        """
        Constructor if the alignment object.
        Makes all the necessary actions upon creation; no need to call any methods on the object.
        All parts of the process are available as variables.

        Inputs:
            sequences (dict) key = Sequence ID, value = Seq()
            window_size (Integer) the size of the window
            step_size (Integer) the size of the step
            makeDebugFiles (Boolean) if True, will create a folder with all the intermediate files


        args:
            self.sequences (Dictionary) Read data from the fasta file
                key = Sequence ID
                value = Seq()

            self.centroidKey (String) Specimen ID of the centroid sequence

            self.centroidSeq (Seq()) The centroid sequence

            self.aligned (Dictionary) Sequences after pairwise alignement
                key = Sequence ID (String) the specimen's ID
                value = Sequence (Seq()) the specimen's DNA sequence

            self.heuristicMSA (Dictionary) Sequences after star style alignement
                key = Sequence ID (String) the specimen's ID
                value = Sequence (Seq()) the specimen's DNA sequence

            self.windowed (Dictionary of Dictionary) Sequences after being windowed
                key = Window ID (String) as "startPosition_endPosition"
                value = (Dictionary)
                    key = Sequence ID (String) the specimen's ID
                    value = Sequence (Seq()) the specimen's DNA sequence

            ##todo
            self.msa (AlignIO())
        """
        self.window_size = window_size
        self.step_size = step_size
        self.makeDebugFiles = makeDebugFiles
        self.bootstrapAmount = bootstrapAmount
        self.sequences = sequences
        self.alignment_method = alignment_method
        self.reference_gene_file = reference_gene_file
        self.fit_method = fit_method

        if self.alignment_method == '1':
            self.centroidKey = self.getSequenceCentroid()[0]
            self.centroidSeq = self.sequences.pop(self.centroidKey)
            self.aligned = self.alignSequencesWithPairwise2()
            if self.fit_method == '1':
                self.heuristicMSA = self.starAlignement()
            elif self.fit_method == '2':
                self.heuristicMSA = self.narrowFitPairwise()
        
        elif self.alignment_method == '2':
            self.heuristicMSA = self.muscleAlign()
        elif self.alignment_method == '3':
            self.heuristicMSA = self.clustalAlign()
        elif self.alignment_method == '4':
            self.heuristicMSA = self.mafftAlign()

        else:
            raise ValueError("Invalid alignment method")
        self.windowed = self.slidingWindow()
        self.msaSet = self.makeMSA()
        
    def getSequenceCentroid(self):
        """
        Method that picks the centroid sequence in a dictionary of sequences

        variables:
            list (list) Needed variable format for using Multiprocessor
        return: a list of:
            resultKey (String)
            resultSum (int)
        """
        seqs = list((self.sequences).items())
        print("\nSearching for the centroid")

        # formats input as a list for the Multiprocess
        seq_pairs_swapped = [((i[0][1], i[0][0]), (i[1][1], i[1][0])) for i in combinations(seqs, r=2)]
        seq_pairs = [list(sum(i, ())) for i in seq_pairs_swapped]                    
        
        # starts all the processes
        align_scores = Multi(seq_pairs, self.ScoreSingle).processingLargeData()

        # formats the multiprocess output back in a dictionnary
        scores = defaultdict(list)
        for pair in align_scores:
            for i in range(0,2):
                scores[pair[i]].append(pair[2])

        centroid_accession = max({key:st.median(val) for key,val in scores.items()})
        centroid_score = st.median(scores[centroid_accession])

        print(f"The centroid is \'{centroid_accession}\' with a median score of {centroid_score}\n")
        
        return [centroid_accession, centroid_score]

    def ScoreSingle(self, args):
        """
        Method the gets only the score of a couple of sequence regarding the
        pairwise alignement

        Args: a list:
            seqA    (Seq()) Sequence A; considered the refenrence
            seqAID  (String) Specimen A's ID
            seqB    (Seq()) Sequence B
            seqBID  (String) Speciment B's ID

        return:
            seqAID  see above
            seqBID  see above
            score   (float) the resulting score of this couple of alignement
        """
        seqA, seqB = args[0], args[2]
        seqAID, seqBID = args[1], args[3]
         
        score = pairwise2.align.globalxx(
            seqA, seqB,
            one_alignment_only=True,
            score_only=True
        )
        return (seqAID, seqBID, score)

    def alignSequencesWithPairwise2(self):
        """
        Method that aligns multiple DNA sequences.
        The first speciment of the dataset is used as the main pivot.
        This method uses parrallel computing.

        Variables:
            seqs (Dictionary) see self.sequences
            list (list) Needed variable format for using Multiprocessor
            result (list) output of all the processes

        Return:
            resultList (Dictionary) see self.aligned

        """
        print("\nStarting sequence alignement")
        seqs = self.sequences

        seq_pairs = []
        for seqXID in seqs.keys():
            seq_pairs.append([self.centroidKey, self.centroidSeq, seqXID, seqs[seqXID]])

        align_scores = Multi(seq_pairs, self.alignSingle).processingLargeData()
        aligned = {}

        # reformats the output in a  dictionnary
        for i in align_scores:
            temp = {}
            temp[i[2]] = Seq((i[1][0].seqA))
            temp[i[0]] = Seq((i[1][0].seqB))
            aligned[str(i[0] + " vs " + i[2])] = temp

        # JUST TO MAKE THE DEBUG FILES
        if self.makeDebugFiles:
            os.mkdir("./debug/1_alignSequences")
            for w in aligned.keys():
                self.dictToFile(aligned[w], str("1_alignSequences/" + w),
                                ".fasta")
        # JUST TO MAKE THE DEBUG FILES

        return aligned
    
    def muscleAlign(self):
        muscle_exe = r'bin/muscle5.1.linux_intel64'
        in_file = self.reference_gene_file
        out_dir = r"bin/tmp/"
        out_file = os.path.splitext(os.path.basename(self.reference_gene_file))[0]
        out_fullname =str(out_dir + out_file + "_muscle_aligned.fasta")
        result = subprocess.run([muscle_exe, "-align", in_file, "-output", out_fullname])
        records = Bio.SeqIO.parse(out_fullname, 'fasta')
        [os.remove(file) for file in glob.glob("bin/tmp/*.fasta")] # Remove temp fasta files
        return {rec.id: str(rec.seq) for rec in records}

    def clustalAlign(self):
        clustal_exe = r"bin/clustalw2"
        in_file = self.reference_gene_file
        fasta_out = r'bin/tmp/clustal_alignment.fasta'
        clustalw_cline = ClustalwCommandline(clustal_exe, infile=in_file, outfile=fasta_out, output="FASTA")
        out, err = clustalw_cline()
        records = Bio.SeqIO.parse(fasta_out, 'fasta')
        [os.remove(file) for file in glob.glob("bin/tmp/*.fasta")] # Remove temp fasta files
        return {rec.id: str(rec.seq) for rec in records}

    def mafftAlign(self):
        mafft_exe = r"bin/mafft-linux64/mafft.bat"
        in_file = self.reference_gene_file
        mafft_cline = MafftCommandline(mafft_exe, input=in_file)
        out, err = mafft_cline()
        fasta_io = StringIO(out)
        records = Bio.SeqIO.parse(fasta_io, 'fasta')
        return {rec.id: str(rec.seq) for rec in records}

    def alignSequencesWithPymuscle5(self):
        """
        Method that aligns multiple DNA sequences using pymuscle5.
        Similar to alignSequenceWithPairwise2, but we've reformatted the return to match the input to the SlidingWindow method.

        Variables:
            fasta_path (str): Path to the FASTA file containing sequences to align.
            records (list): List of SeqRecord objects containing sequences from the FASTA file.
            sequences (list): List of pymuscle5.Sequence objects for alignment.
            aligned (dict): Dictionary to store aligned sequences.
            aligner (pymuscle5.Aligner): PyMuscle5 aligner object.
            msa (pymuscle5._muscle.Alignment): Result of the sequence alignment.
            seq (pymuscle5._muscle.Sequence): Aligned sequence object.
            seq_id (str): Decoded identifier of the aligned sequence.
            seq_data (str): Decoded aligned sequence data.
            heuristicMSA (dict): Dictionary to store the aligned sequences (see self.heuristicMSA).

        Return:
            heuristicMSA (dict): Dictionary containing aligned sequences (see self.heuristicMSA).
        """

        print("\nStarting sequence alignment with pymuscle5")
        # Lecture des séquences à partir du fichier FASTA
        fasta_path = self.reference_gene_file
        records = list(Bio.SeqIO.parse(fasta_path, "fasta"))

        # Création des séquences PyMuscle5
        sequences = [
            pymuscle5.Sequence(record.id.encode(), bytes(record.seq))
            for record in records
        ]
        
        aligned = {}

        # Alignement des séquences
        aligner = pymuscle5.Aligner()
        msa = aligner.align(sequences)

        for seq in msa.sequences:
            seq_id = seq.name.decode()
            seq_data = seq.sequence.decode()
            aligned[seq_id] = seq_data

        self.heuristicMSA = aligned
        return self.heuristicMSA

    def alignSingle(self, args):
        """
        Method that aligns two DNA sequences using the pairwise2 algorithm.

        Args:
            args (list)
                scID    (String) The centroid sequence ID to compare to
                sc      (Seq()) The DNA sequence of scID
                seqBID  (String) The sequence ID to compare with
                seqB    (Seq()) The DNA sequence of seqBID

        Return: (list)
            seqBID see above
            aligned (List) The list containing the results.
            scID see above
        """
        scID, seqBID = args[0], args[2]
        sc, seqB = args[1], args[3]
        
        aligned = pairwise2.align.globalxx(sc, seqB, one_alignment_only=True)
        return [seqBID, aligned, scID]

    def narrowFitPairwise(self):
        """Fit length of a centroid sequence and its pairwise aligned sequences
        
        The length of each sequence from the pairwise alignment are set equal by 
        inserting dash (-) in most appropriate location of a given sequence.

        Parameters:
        -----------
        alignment: dict of nested dict
            {accession couple #1 : {Centroid Acc:Centroid Aligned Seq, Non-centroid Acc #1: non-centroid Aligned Seq #1}, 
            ... , 
            {accession couple #n : {Centroid Acc:Centroid Aligned Seq, Non-centroid Acc #n: non-centroid Aligned Seq #n}}
        
        Return:
        -------
        A dictionary of all accessions and their fitted aligned sequences.
        """
        seqs = self.getAlignSeqs()
        max_len = max(self.getAlignSeqLens())
        for nucleo_i in range(0, max_len):
            for seq_i in range(0, len(seqs)):        
                if self.isCurrentCharDash(seqs, seq_i, nucleo_i):
                    seqs = self.insertDashToShorterSeq(seqs, nucleo_i)
        seqs = self.appendDashToShorterSeqs(seqs, max_len)
        return self.mergeFitPairwise(seqs)

    def getAlignSeqs(self):
        """Extract all sequences aligned using a pairwise alignment

        Parameters:
        -----------
        alignment: see fitPairwise(alignment) docstring

        Return:
        -------
        List of sequences aligned through pairwise alignment
        """
        seqs = []
        for alignment in self.aligned:
            seqs.append([str(seq) for seq in self.aligned[alignment].values()])
        return list(sum(seqs, []))


    def getAlignSeqLens(self):
        """Get length of all sequences aligned using a pairwise alignment

        Parameters:
        -----------
        alignment: see fitPairwise(alignment) docstring

        Return:
        -------
        List of the length of each aligned sequences
        """
        return [len(seq) for seq in self.getAlignSeqs()]


    def getAlignCouple(self):
        """Get nested couple accessions and their respective sequences

        Parameters:
        -----------
        alignment: see fitPairwise(alignment) docstring
        
        Return:
        -------
        List of paired accessions and their aligned sequences
        """
        return [val for val in list(self.aligned.values())]


    def extractOneAlignAcc(self, nest_ord = 0):
        """Extract the accession from a nested alignment couple

        Parameters:
        -----------
        alignment: see fitPairwise(alignment) docstring
        nest_ord, int, optional: 
            The position of the nested accessions (Default = 0 (centroid), 1 (aligned sequence))

        Return:
        -------
        The list of either centroid (nest_ord = 0 (Default)) or non-centroid (nest_ord = 1) 
        accessions of a group of sequences aligned throug pairwise alignment.
        """
        try:
            return [list(i)[nest_ord] for i in self.getAlignCouple()]
        
        # Return the centroid sequence if an invalid position is queried
        except IndexError:
            return [list(i)[0] for i in self.getAlignCouple()]


    def isCurrentCharDash(self, seqs, seq_i, ch_i):
        """Assess whether the character at current cursor position is a dash
        
        Parameters:
        -----------
        seqs,  list: aligned sequences to fit
        seq_i, int:  index of the current sequence
        ch_i,  int:  index of the currenct character

        Return:
        -------
        True if the current character assessed is a dash, False otherwise
        """
        try:
            return seqs[seq_i][ch_i] == '-'
        except IndexError:
            return False


    def insertDashToShorterSeq(self, seqs, ch_i):
        """Insert a dash at the current position of a sequence
        
        Insert a dash (-) character in a sequence if its length is shorter 
        than the longest one in the group of aligned sequence.

        Parameters:
        -----------
        seqs,  list:    aligned sequences to fit
        seq_i, int:     index of the current sequence

        Return:
        -------
        List, The fitted sequences of a pairwise alignment
        """
        for seq_j in range(0, len(seqs)):
            try:
                if (len(seqs[seq_j]) < max(self.getAlignSeqLens())) & (seqs[seq_j][ch_i] != '-'): 
                    seqs[seq_j] = seqs[seq_j][:ch_i] + '-' + seqs[seq_j][ch_i:]
            except IndexError:
                    seqs[seq_j] = seqs[seq_j][:ch_i] + '-'
        return seqs        


    def mergeFitPairwise(self, seqs):
        """Generate a dictionary of all accessions and their fitted sequences
        
        Parameters:
        -----------
        alignment: see fitPairwise(alignment) docstring
        seqs,  list:    aligned sequences to fit

        Return:
        -------
        Dict, Group of accessions and their fitted sequences from a pairwise alignment
        """
        centroid = {list(set(self.extractOneAlignAcc()))[0]:seqs[0]}
        non_centroid = dict(zip(self.extractOneAlignAcc(1), seqs[1::2]))    
        return centroid | non_centroid


    def appendDashToShorterSeqs(self, seqs, max_len):
        """Append dash to all sequences shorter than the longest one from a list of sequences
        
        Parameters:
        -----------
        seqs, list:  List of fitted sequences post pairwise alignment
        max_len int: Length of the longest aligned sequence, including the blank/dash
        
        Return:
        -------
        List of sequences with dash appended where applicable
        """
        return [f"{str(seq):-<{max_len}}" for seq in seqs]

    def starAlignement(self):
        """
        Method that combs through all the pairwise alignments couples and makes
        it so that every sequenced is aligned with every other sequences. If a
        "-" is found in the seqA of a pair, but not another, it is inserted
        into every other ones.

        ex.:
            pair1:          pair2:

            seqA1: TACTAC   seqA2: TAC-TAC
            seqB1: TACTAC   seqB2: TACTTAC

            becomes:
            seqA1: TAC-TAC   seqA2: TAC-TAC
            seqB1: TAC-TAC   seqB2: TACTTAC

            and outputs:
            seqA : TAC-TAC   #now combines SeqA1 and SeqA2
            seqB1: TAC-TAC
            seqB2: TACTTAC

            then, we compare the aligned set with the next pair:

            SeqA : TAC-TAC  seqA3: TACTA-C
            seqB1: TAC-TAC  seqB3: TACTAAC
            seqB2: TACTTAC

            wich makes:
            SeqA : TAC-TA-C  seqA3: TAC-TA-C
            seqB1: TAC-TA-C  seqB3: TAC-TAAC
            seqB2: TACTTA-C

            and outputs:
            SeqA : TAC-TA-C     #now combines SeqA1, SeqA2 and SeqA3
            seqB1: TAC-TA-C
            seqB2: TACTTA-C
            seqB3: TAC-TAAC

            over and over again

        Return:
            starAlign (dict) see self.heuristicMSA
        """
        scKey = self.centroidKey
        starAlign = {}

        for k in self.aligned.keys():
            # couple is SeqA and SeqB of a pairwise alignement
            couple = self.aligned[k]

            a = list(couple.keys())
            a.remove(scKey)
            sNewKey = a[0]   # SeqB ID, *not* the reference

            starAlign[scKey] = couple[scKey]  # SeqA, the reference
            starAlign[sNewKey] = couple[sNewKey]  # SeqB, *not* the reference

            if len(starAlign) > 2:
                starAlign = self.merge(starAlign, scKey, sNewKey)

            starAlign["temp"] = starAlign[scKey]  # SeqA, the *old* reference
        starAlign.pop("temp")

        # JUST TO MAKE THE DEBUG FILES
        if self.makeDebugFiles:
            os.mkdir("./debug/2_starAlignement")
            self.dictToFile(starAlign, "2_starAlignement/starAligned",
                            ".fasta")
        # JUST TO MAKE THE DEBUG FILES

        return starAlign

    def merge(self, result, k1, k2):
        """
        Method that loops through each position of two strings ans compares the Chars.

        Arguments:
            result (dict) the dictionnary of objects to compare;
                contains only object that have already been aligned + a new pair to align
                can be refered to as "aligned set"
            k1 (String) The Key of the object we want compared
            k2 (String) The Key of the object we want compared
        Variables:
            minLen  (int)   The number of char in the smallest of the two strings
            pos     (int)   The char position at wich we are now; it loops
            nChar   (char)  The char from k1
            tChar   (char)  The char from K2
            keylist (list)  Ultimatly, contains all the keys of the object that need to change
        Return:
            result (dict)   The same object we started with, but with one more aligned pair inside.
        """
        newRef = result[k1]
        tempRef = result["temp"]
        minLen = 1
        pos = 0
        while pos < minLen:
            # The sequence length could change at each iteration
            # these assignemnts needs to be done each loop to get
            # to the true end and not to skip the '-' we just added
            newRef = result[k1]
            tempRef = result["temp"]
            minLen = min(len(newRef), len(tempRef))

            nChar = newRef[pos]
            tChar = tempRef[pos]

            if nChar != tChar:

                # - found in the new ref, change all but the 2 new elements
                if nChar == '-':
                    keyList = list(result.keys())
                    keyList.remove(k1)
                    keyList.remove(k2)

                # - found in the old ref; change the 2 new elements
                elif tChar == '-':
                    keyList = [k1, k2]
                else:
                    errStr = str(
                        "Alignement error. Merge() found \"" + str(nChar) +   \
                        "\" and \"" + str(tChar) + "\" " + "at position " +   \
                        str(pos) + " of two versions of the centroid " +      \
                        "sequences\n" + "Please check the previous methods" + \
                        " and ensure the pairwise alignemnt is correct" +     \
                        "\nCentroid ID: " + str(self.centroidKey) +           \
                        "\nPairwise seq ID" + " last inserted: " + str(k2)
                    )

                    raise Exception(errStr)

                result = self.insertDash(result, pos, keyList)

            pos += 1

        return result

    def insertDash(self, dict, pos, keyList):
        """
        Method that inserts a "-" at [pos] in a string at every Key in a dict

        Arguments:
            dict    (dict)  contains many objects as:
                key = (string)
                values = (string)
            pos     (int)   the char position at wich to insert
            keyList (list)  list of keys of objects to modify
        Variables:
            char    (char)  The char to insert
        Return:
            dict    (dict)  The same we started with, with the modifications
        """
        for k in keyList:
            char = '-'
            s = dict[k]
            s = s[:pos] + char + s[pos:]
            dict[k] = s
        return dict


    def slidingWindow(self):
        """
        Method that slices all the sequences in a dictionary to a specific window (substring)

        ex.:
            step_size=3
            window_size=5

            123 : CGGCTCAGCT  -->   123_3_7 : GCTCA
            456 : TAGCTTCAGT  -->   456_3_7 : GCTTC

        Args:
            alignedSequences (Dictionary)
                Key (String) is the ID of the specimen
                Data (Seq(String)) is the specimen's DNS sequence
            others* (var) see param.yaml

        Return:
            resultDict (Dictionary)
                Key is originalKey_i_j
                    originalKey = the name of the key before the window
                    i = The starting position of the window, relative to the original sequence
                    j = The ending position of the window, relative to the original sequence
        """
        step = self.window_size
        windowed_alignment = dict()
        seq_len = max([len(h) for h in self.heuristicMSA.values()])
        
        paddedMSA = {key:str(val).ljust(seq_len, "-") for key,val in self.heuristicMSA.items()}

        for i in range(0, seq_len, step):
            if i + step < seq_len:
                windowed_alignment[f"{i}_{i + step - 1}"] = {key:val[i:i + step - 1] for key, val in paddedMSA.items()}
            else:
                windowed_alignment[f"{i}_{seq_len-1}"] = {key:val[i:i + seq_len - 1] for key, val in paddedMSA.items()}

        # JUST TO MAKE THE DEBUG FILES
        if self.makeDebugFiles:
            os.mkdir("./debug/3_slidingWindow")
            for w in windowed_alignment.keys():
                self.dictToFile(windowed_alignment[w], "3_slidingWindow/" + w,
                                ".fasta")
        # JUST TO MAKE THE DEBUG FILES

        return windowed_alignment

    def dictToFile(self, dict, filename, ext):
        """
        Debuging method that creates files from a dictonnary of sequences.
        File is put in the debug file of the cwd

        arguments
            dict        (dict)      the objects to write in the file
                key = (string)
                values = (string)
            filename    (String)    the name of the future file
            ext         (String)    the file extension

        return:
            dict        (dict)       see dict from arguments
        """
        dir = "./debug"
        if not os.path.exists(dir):
            os.mkdir(dir)

        f = open(dir + "/" + filename + ext, "w")
        for key in dict.keys():
            f.write(">" + str(key) + "\n")
            f.write(str(dict[key] + "\n"))
        return dict

    def makeMSA(self):
        """
        Method that create a dictionnary of Multiple Sequence Alignment(MSA)
        objects from bioPython. Each entry in the dictionnary is a MSA object
        of a single sliding window.

        return
            msaSet (dict)
                key (String) the window name
                value (AlignIO) the MSA object
        """
        msaSet = {}
        for windowSet in self.windowed.keys():
            data = ""
            window = self.windowed[windowSet]
            for seq in window.keys():
                data += str(">" + seq + "\n" + window[seq] + "\n")
            msaSet[windowSet] = AlignIO.read(StringIO(data), "fasta")

        return msaSet

    def fileToDict(filename, ext):
        """
        Method that reads a fasta file and returns a dictionnary of Seq objects

        arguments:
            filename    (String)    the name of the file
            ext         (String)    the file extension

        return:
            dict        (dict)
                key = (string)
                values = (string)
        """
        f = open(Path(filename + ext), "r")
        dict = {}
        for line in f:
            if line[0] == ">":
                key = line[1:-1]
                dict[key] = ""
            else:
                dict[key] += line[:-1]
        f.close()
        return dict

    def fileToAlignIO(filename, ext):
        """
        Method that reads a fasta file and returns a AlignIO object

        arguments:
            filename    (String)    the name of the file
            ext         (String)    the file extension

        return:
            alignIO     (AlignIO)   the AlignIO object
        """
        f = open(Path(filename + ext), "r")
        data = ""
        for line in f:
            data += line
        f.close()
        alignIO = AlignIO.read(StringIO(data), "fasta")
        return alignIO
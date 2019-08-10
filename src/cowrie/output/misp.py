import sys
import warnings
from io import BytesIO
from functools import wraps
from pymisp import MISPEvent, MISPSighting
from twisted.python import log

import cowrie.core.output
from cowrie.core.config import CowrieConfig

try:
    from pymisp import ExpandedPyMISP as PyMISP
except ImportError:
    from pymisp import PyMISP as PyMISP


# PyMISP is very verbose regarding Python 2 deprecation
def ignore_warnings(f):
    @wraps(f)
    def inner(*args, **kwargs):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("ignore")
            response = f(*args, **kwargs)
        return response
    return inner


class Output(cowrie.core.output.Output):
    """
    MISP Upload Plugin for Cowrie.

    This Plugin creates a new event for unseen file uploads
    or adds sightings for previously seen files.
    The decision is done by searching for the SHA 256 sum in all matching attributes.
    """

    @ignore_warnings
    def start(self):
        """
        Start output plugin
        """
        misp_url = CowrieConfig().get('output_misp', 'base_url')
        misp_key = CowrieConfig().get('output_misp', 'api_key')
        misp_verifycert = ("true" == CowrieConfig().get('output_misp', 'verify_cert').lower())
        self.misp_api = PyMISP(url=misp_url, key=misp_key, ssl=misp_verifycert, debug=False)
        self.is_python2 = sys.version_info[0] < 3


    def stop(self):
        """
        Stop output plugin
        """
        pass


    def write(self, entry):
        """
        Push file download to MISP
        """
        if entry['eventid'] == 'cowrie.session.file_download':
            file_sha_attrib = self.find_attribute("sha256", entry["shasum"])
            if file_sha_attrib:
                # file is known, add sighting!
                log.msg("File known, add sighting!")
                self.add_sighting(entry, file_sha_attrib)
            else:
                # file is unknown, new event with upload
                log.msg("File unknwon, add new event!")
                self.create_new_event(entry)


    @ignore_warnings
    def find_attribute(self, attribute_type, searchterm):
        """
        Returns a matching attribute or None if nothing was found.
        """
        result = self.misp_api.search(
            controller="attributes",
            type_attribute=attribute_type,
            value=searchterm
        )

        # legacy PyMISP returns the Attribute wrapped in a response
        if self.is_python2:
            result = result["response"]

        if result["Attribute"]:
            return result["Attribute"][0]
        else:
            return None


    @ignore_warnings
    def create_new_event(self, entry):
        self.misp_api.upload_sample(
            entry["shasum"],
            entry["outfile"],
            None,
            distribution=1,
            info="Uploaded by: {} (Cowrie)".format(entry["sensor"]),
            analysis=0,
            threat_level_id=2
        )


    @ignore_warnings
    def add_sighting(self, entry, attribute):
        if self.is_python2:
            self.misp_api.sighting(
                uuid=attribute["uuid"],
                source= "{} (Cowrie)".format(entry["sensor"])
            )
        else:
            sighting = MISPSighting()
            sighting.source = "{} (Cowrie)".format(entry["sensor"])
            self.misp_api.add_sighting(sighting, attribute)

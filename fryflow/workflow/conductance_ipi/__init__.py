NVT_in_ipi_template = """
<simulation verbosity="high">
  <output prefix="simulation">
      <properties stride='10' filename='out'>
        [ step, time{{picosecond}}, temperature{{kelvin}}, density{{g/cm3}} ]
      </properties>
      <trajectory filename='pos' stride='{xv_stride}' cell_units='angstrom'> positions{{angstrom}} </trajectory>
      <trajectory filename='vel' stride='{xv_stride}' cell_units='angstrom'> velocities{{m/s}} </trajectory>
<checkpoint filename="chk" stride="{check_stride}" overwrite="true"/>
  </output>
  <prng><seed> {seed}</seed></prng>
  <total_steps>{md_steps}</total_steps>
    <ffsocket mode='unix' name='dp'>
         <port> 1234 </port>
         <address> {MD_addr} </address>
   </ffsocket>  
<system>
    <initialize nbeads="{n_beads}">
      <file mode="xyz"> {initial_state} </file>
      <velocities mode='thermal' units='kelvin'> {temperature} </velocities>
    </initialize>
    <forces>
      <force forcefield="dp"> </force>
    </forces>
    <ensemble>
      <temperature units="kelvin"> {temperature} </temperature>
    </ensemble>
    <motion mode="dynamics">
      <fixcom>True</fixcom>
      <dynamics mode="{DYNAMICS}">
        <timestep units="femtosecond"> {time_step} </timestep>
        <thermostat mode="langevin">
        <tau units="femtosecond">50</tau> 
        </thermostat>
      </dynamics>
    </motion>
  </system>
</simulation>
"""

NVE_in_ipi_template = """
<simulation verbosity="high">
  <output prefix="simulation">
      <properties stride='10' filename='out'>
        [ step, time{{picosecond}}, potential{{electronvolt}}, kinetic_md{{electronvolt}},  temperature{{kelvin}}, density{{g/cm3}} ]
      </properties>
      <trajectory filename='x_centroid' stride='5' cell_units='angstrom'> x_centroid{{angstrom}} </trajectory>
      <trajectory filename='v_centroid' stride='5' cell_units='angstrom'> v_centroid{{m/s}} </trajectory>
<checkpoint filename="chk" stride="{check_stride}" overwrite="true"/>
  </output>
  <total_steps>{md_steps}</total_steps>
    <ffsocket mode='unix' name='dp'>
         <port> 1234 </port>
         <address> {MD_addr} </address>
   </ffsocket>
<system>
    <initialize nbeads="{n_beads}">
      <file mode="xyz"> pos_bead_00.xyz </file>
{bead_init}
    </initialize>
    <forces>
      <force forcefield="dp"> </force>
    </forces>
    <motion mode="dynamics">
      <fixcom>True</fixcom>
      <dynamics mode="nve">
        <timestep units="femtosecond"> {time_step} </timestep>
      </dynamics>
    </motion>
  </system>
</simulation>
"""

bead_init_line = """
      <positions mode="xyz" bead="{i_bead:02}"> pos_bead_{i_bead:02}.xyz </positions>
      <velocities mode="xyz" units="m/s/bead" bead="{i_bead:02}"> vel_bead_{i_bead:02}.xyz  </velocities>
"""
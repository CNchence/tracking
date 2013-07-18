import numpy as np
import trackingpy


class Cloth(object):
  def __init__(self, res_x, res_y, len_x, len_y, init_center):
    self.res_x, self.res_y, self.len_x, self.len_y, self.init_center = res_x, res_y, len_x, len_y, init_center

    # initialize node positions
    assert self.res_x >= 2 and self.res_y >= 2
    self.num_nodes = self.res_x * self.res_y

    init_pos = np.zeros((self.num_nodes, 3))
    init_pos[:,:2] = np.dstack(np.meshgrid(np.linspace(0, self.len_x, self.res_x), np.linspace(0, self.len_y, self.res_y))).reshape((-1, 2))
    init_pos -= init_pos.mean(axis=0) - self.init_center
    masses = np.ones(self.num_nodes)

    # create mass-spring system
    sim_params = trackingpy.SimulationParams()
    sim_params.dt = .01
    sim_params.solver_iters = 20
    sim_params.gravity = np.array([0, 0, -9.8])
    sim_params.damping = 1

    self.sys = trackingpy.MassSystem(init_pos, masses, sim_params)

    # anchors for testing
    for i in range(self.res_x):
      self.sys.add_anchor_constraint(i, init_pos[i])

    self._add_structural_constraints(init_pos)

    self.sys.randomize_constraints()

  def _add_structural_constraints(self, init_pos):
    self.distance_constraints = []
    def add_single(i, j):
      self.sys.add_distance_constraint(i, j, np.linalg.norm(init_pos[i] - init_pos[j]))
      self.distance_constraints.append((i, j))

    for i in range(self.num_nodes):
      x, y = self._i_to_xy(i)

      if x+1 < self.res_x:
        add_single(i, self._xy_to_i(x+1,y))

      if y+1 < self.res_y:
        add_single(i, self._xy_to_i(x,y+1))

      if x+1 < self.res_x and y+1 < self.res_y:
        add_single(i, self._xy_to_i(x+1,y+1))

      if x+1 < self.res_x and y-1 >= 0:
        add_single(i, self._xy_to_i(x+1,y-1))

  def _i_to_xy(self, i): return i % self.res_x, i // self.res_x
  def _xy_to_i(self, x, y): return y*self.res_x + x

  def step(self):
    self.sys.step()

  def get_node_positions(self):
    return self.sys.get_node_positions()

  def get_distance_constraints(self):
    return self.distance_constraints

def make_table_xml(translation, extents):
  xml = """
<Environment>
<KinBody name="table">
  <Body type="static" name="table_link">
    <Geom type="box">
      <Translation>%f %f %f</Translation>
      <extents>%f %f %f</extents>
      <diffuseColor>.96 .87 .70</diffuseColor>
    </Geom>
  </Body>
</KinBody>
</Environment>
""" % (translation[0], translation[1], translation[2], extents[0], extents[1], extents[2])
  return xml

def main():
  import openravepy
  import trajoptpy
  env = openravepy.Environment()
  viewer = trajoptpy.GetViewer(env)

  env.LoadData(make_table_xml(translation=[0, 0, -.05], extents=[1, 1, .05]))

  np.random.seed(0)
  cloth = Cloth(res_x=10, res_y=15, len_x=.5, len_y=1., init_center=np.array([0, 0, .5]))


  # add above-table constraints
  for i in range(cloth.num_nodes):
    cloth.sys.add_plane_constraint(i, np.array([0, 0, 0]), np.array([0, 0, 1]))

  # from timeit import Timer
  # print 'timing'
  # t = Timer(lambda: cloth.step())
  # print t.timeit(number=100)
  # raw_input('done timing')

  iters = 100000

  log = np.empty((iters, cloth.num_nodes, 3))

  for i in range(iters):
    print i
    cloth.step()
    pos = cloth.get_node_positions()
    handles = [env.plot3(pos, 5)]
    for node_i, node_j in cloth.get_distance_constraints():
      handles.append(env.drawlinelist(np.asarray([pos[node_i], pos[node_j]]), 1, [0,1,0]))
    viewer.Step()

    log[i,:,:] = pos

  # import cPickle
  # with open('out.pkl', 'w') as f:
  #   cPickle.dump(log, f)


if __name__ == '__main__':
  main()
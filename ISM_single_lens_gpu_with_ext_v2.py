from globals import *
import functions_gpu
import tests
import propagators_gpu as prop

matplotlib.use('TkAgg')

##########################################
##########################################
####      v00_system parameters:      ####
##########################################
##########################################


v00_system = System()
v00_system.wave_length = 632e-9
v00_system.f = 30e-2
v00_system.u = 2 * v00_system.f
v00_system.v = round((v00_system.u * v00_system.f) / (v00_system.u - v00_system.f), 5)
v00_system.lens_radius = 10e-1
v00_system.lens_center_pos = [0, 0]
v00_system.length_x = 10e-1

v00_system.wave_length = torch.tensor(v00_system.wave_length).to(device)
v00_system.f = torch.tensor(v00_system.f).to(device)
v00_system.u = torch.tensor(v00_system.u).to(device)
v00_system.v = torch.tensor(v00_system.v).to(device)
v00_system.lens_radius = torch.tensor(v00_system.lens_radius).to(device)
v00_system.lens_center_pos = torch.tensor(v00_system.lens_center_pos).to(device)
v00_system.length_x = torch.tensor(v00_system.length_x).to(device)

###############################
###############################
### setting up field matrix ###
###############################
###############################
#
##################################
# option 1: crate field matrix: ##
##################################
max_dim = 99
dim_x = dim_y = max_dim
# dim_y = int(dim_x / 2)
field = np.ones([dim_y, dim_x])
# field = np.ones([dim_y, dim_x])
point = [dim_x // 2, dim_y // 2]
field[point[1], point[0]] = 0
del point, dim_x, dim_y, max_dim

#
# ###############################################
# ## option 2: crate field matrix with points: ##
# ###############################################
# dim_x = dim_y = 83
# dim_y = 44
#
# num_x_points = 1
# num_of_x_intervals = num_x_points + 1
# num_of_pix_in_x_interval = (dim_x - num_x_points) / num_of_x_intervals
# num_of_pix_in_x_interval = np.ceil(num_of_pix_in_x_interval)
# dim_x = num_of_x_intervals * num_of_pix_in_x_interval + num_x_points
# dim_x = int(dim_x)
#
# num_y_points = 1
# num_of_y_intervals = num_y_points + 1
# num_of_pix_in_y_interval = (dim_y - num_y_points) / num_of_y_intervals
# num_of_pix_in_y_interval = np.ceil(num_of_pix_in_y_interval)
# dim_y = num_of_y_intervals * num_of_pix_in_y_interval + num_y_points
# dim_y = int(dim_y)
#
# field = np.zeros([dim_y, dim_x])
#
# del num_of_x_intervals, num_of_y_intervals, dim_x, dim_y
#
# column = 0
# for x_point in np.arange(num_x_points):
#     column += num_of_pix_in_x_interval
#     row = 0
#     for y_point in np.arange(num_y_points):
#         row += num_of_pix_in_y_interval
#         # print([int(row), int(column)])
#         field[int(row), int(column)] = 1
#         row += 1
#     column += 1
#
# del x_point, y_point, row, column, num_x_points, num_y_points, num_of_pix_in_x_interval, num_of_pix_in_y_interval

# #######################################
# ## option 3: crate field from image: ##
# #######################################
# field, file_path = functions_gpu.getimage()
# del file_path


# #######################################
# ## option 4: cut part of the pic: ##
# #######################################
# image, file_path = functions_gpu.getimage()
# left, upper, right, lower = functions_gpu.get_points_to_crop(file_path)
# field = image[upper:lower, left:right]
# del left, upper, right, lower, image, file_path


# #################################
# ## option: save field as image ##
# #################################
# z = (field * 255).astype(np.uint8)
# img = Image.fromarray(z, mode='L')
# img.save(file_path + "smallnum6.jpeg")
#
# del left, upper, right, lower
# del file_path, image


# ##################
# ## resize image ##
# ##################
# dim_y, dim_x = field.shape
# max_dim = int(1 * np.max(field.shape))
# if dim_y > dim_x:
#     ratio = dim_x / dim_y
#     dim_y = max_dim
#     dim_x = int(np.round((ratio * max_dim)))
# else:
#     ratio = dim_y / dim_x
#     dim_x = max_dim
#     dim_y = int(np.round(ratio * max_dim))
#
# dim = (dim_x, dim_y)
# field = cv2.resize(field, dim, interpolation=cv2.INTER_AREA)
# field[field > 0.3] = 1
# field[field <= 0.3] = 0
# del max_dim, ratio, dim, dim_x, dim_y

start = time.time()

#########################################
### real space coordinates definition ###
###        all units in [meter]       ###
#########################################
v01_initial_field = Field(torch.from_numpy(field))
z = 0
v01_initial_field.z = torch.tensor(z).to(device)
del field, z

v01_initial_field.length_x = v00_system.length_x  # real length in x dimension
v01_initial_field.step = v01_initial_field.length_x / (v01_initial_field.field.shape[1] - 1)

v01_initial_field.length_y = v01_initial_field.step * (
        v01_initial_field.field.shape[0] - 1)  # real length in y dimension

## getting the coordinates such that 0 is in the middle
start_x = -0.5 * v01_initial_field.length_x
end_x = 0.5 * v01_initial_field.length_x

start_y = 0.5 * v01_initial_field.length_y
end_y = -0.5 * v01_initial_field.length_y

v01_initial_field.x_coordinates = torch.linspace(start_x, end_x, v01_initial_field.field.shape[1]).to(device)
v01_initial_field.y_coordinates = torch.linspace(start_y, end_y, v01_initial_field.field.shape[0]).to(device)
v01_initial_field.mesh = torch.meshgrid(v01_initial_field.y_coordinates, v01_initial_field.x_coordinates)
v01_initial_field.extent = torch.tensor([start_x, end_x, end_y, start_y]).to(device)
v01_initial_field.padding_size = torch.tensor(0).to(device)

del start_x, start_y, end_x, end_y

##################
## show field ##
##################
fig0, ax0 = plt.subplots()
im0 = ax0.imshow(v01_initial_field.field.to('cpu').numpy(), extent=v01_initial_field.extent.to('cpu').numpy())
ax0.set_title('initial field')
plt.show(block=False)
del fig0, ax0, im0

####################################
### padding the field with zeros ###
####################################
small_padding_size = 50
small_padding_size = torch.tensor(small_padding_size).to(device)
v02_small_padded_field = functions_gpu.pad(v01_initial_field, small_padding_size)
v03_filtered_small_padded_field = copy.deepcopy(v02_small_padded_field)
v03_field = v03_filtered_small_padded_field.field.to('cpu').numpy()
v03_field = gaussian_filter(v03_field, sigma=np.sqrt(1))
v03_filtered_small_padded_field.field = torch.from_numpy(v03_field).to(device)

# show padded field
fig1, ax1 = plt.subplots()
im1 = ax1.imshow(v03_filtered_small_padded_field.field.to('cpu').numpy(),
                 extent=v03_filtered_small_padded_field.extent.to('cpu').numpy())
ax1.set_title('filtered_small_padded_field')
del fig1, ax1, im1, small_padding_size, v03_field

padding_size = 250
padding_size = torch.tensor(padding_size).to(device)
v04_padded_object = functions_gpu.pad(v03_filtered_small_padded_field, padding_size)

# show padded field
fig1, ax1 = plt.subplots()
im1 = ax1.imshow(v04_padded_object.field.to('cpu').numpy(), extent=v04_padded_object.extent.to('cpu').numpy())
ax1.set_title('padded_filtered_field')
plt.show(block=False)
fig1.colorbar(im1)
del fig1, ax1, im1, padding_size

v04_2_padded_object = copy.deepcopy(v04_padded_object)

# Perform 2D Fourier Transform on the complex matrix
matrix_fft = torch.fft.fft2(v04_2_padded_object.field)

fig0, ax0 = plt.subplots()
im0 = ax0.imshow(np.abs(matrix_fft.to('cpu').numpy()),
                 extent=v04_2_padded_object.extent.to('cpu').numpy())
ax0.set_title('matrix_fft')
plt.show(block=False)
fig0.colorbar(im0)
del fig0, ax0, im0

# Define the number of harmonics to keep in each dimension
N = v04_2_padded_object.field.shape[0]
M = v04_2_padded_object.field.shape[1]
n_harmonics_x = N // 2
n_harmonics_y = M // 2

# Create a new zero-filled complex tensor with dimensions 2N x 2M
filtered_fft = torch.zeros(2 * N, 2 * M, dtype=torch.complex64).to(device)

# Copy the selected harmonics from the original FFT matrix to the new, larger FFT matrix
# Keep the first n_harmonics_x and n_harmonics_y harmonics in each quadrant
filtered_fft[:n_harmonics_x, :n_harmonics_y] = matrix_fft[:n_harmonics_x, :n_harmonics_y]
filtered_fft[-n_harmonics_x:, :n_harmonics_y] = matrix_fft[-n_harmonics_x:, :n_harmonics_y]
filtered_fft[:n_harmonics_x, -n_harmonics_y:] = matrix_fft[:n_harmonics_x, -n_harmonics_y:]
filtered_fft[-n_harmonics_x:, -n_harmonics_y:] = matrix_fft[-n_harmonics_x:, -n_harmonics_y:]

# Perform 2D Inverse Fourier Transform on the filtered, larger FFT matrix
extrapolated_matrix = torch.fft.ifft2(filtered_fft)

v04_2_padded_object.field = extrapolated_matrix

fig0, ax0 = plt.subplots()
im0 = ax0.imshow(np.abs(v04_2_padded_object.field.to('cpu').numpy()),
                 extent=v04_2_padded_object.extent.to('cpu').numpy())
ax0.set_title('object ext')
plt.show(block=False)
fig0.colorbar(im0)
del fig0, ax0, im0

##############################
##############################
#####     simulation     #####
##############################
##############################


# ########################
# ##   test   ###
# ########################
# start_time = time.time()
# tests.test(v01_initial_field, v00_system, small_padding_size + padding_size, v04_padded_object)
# end_time = time.time()
# elapsed_time = end_time - start_time
# print(f'Elapsed time: {elapsed_time} seconds')
# del padding_size, small_padding_size

"""
x_coordinates = padded_coordinates[0]
y_coordinates = padded_coordinates[1]
extent = padded_extent
"""

##############################
###   wide field imaging   ###
##############################
# propagation u
field_in = copy.deepcopy(v04_padded_object)
z_out = v00_system.u
v05_field_before_lens = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=0)

"""
v05_field_before_first_lens = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=1)
"""
del field_in, z_out

# ###########################################
# ###   wide field imaging - with steps   ###
# ###########################################
# num_of_steps = 10
# for iteration in np.arange(num_of_steps):
#     rel_dist = (iteration + 1) / num_of_steps * z_out
#     v05_field_before_lens = prop.distance_z(field_in, rel_dist, v00_system.wave_length, plot=1)
#     field_in = copy.deepcopy(v05_field_before_lens)
#

# Lens
field_in = copy.deepcopy(v05_field_before_lens)
v06_field_after_lens = prop.thin_lens(field_in, v00_system.wave_length, v00_system.lens_radius,
                                      v00_system.lens_center_pos, v00_system.f, plot=0)

"""
v06_field_after_first_lens = prop.thin_lens(field_in, v00_system.wave_length, v00_system.lens_radius, v00_system.lens_center_pos, v00_system.f, plot=1)
"""
del field_in

# propagation v to imaging plane
field_in = copy.deepcopy(v06_field_after_lens)
z_out = field_in.z + v00_system.v
v07_image_wide_field_imaging = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=1)
"""
v07_image_wide_field_imaging = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=1)
"""
del field_in, z_out

fig0, ax0 = plt.subplots()
im0 = ax0.imshow(np.abs(v07_image_wide_field_imaging.field.to('cpu').numpy()),
                 extent=v07_image_wide_field_imaging.extent.to('cpu').numpy())
ax0.set_title('wide field imaging')
plt.show(block=False)
fig0.colorbar(im0)
del fig0, ax0, im0

v07_2_image_wide_field_imaging = copy.deepcopy(v07_image_wide_field_imaging)

# Perform 2D Fourier Transform on the complex matrix
matrix_fft = torch.fft.fft2(v07_2_image_wide_field_imaging.field)

fig0, ax0 = plt.subplots()
im0 = ax0.imshow(np.abs(matrix_fft.to('cpu').numpy()),
                 extent=v07_image_wide_field_imaging.extent.to('cpu').numpy())
ax0.set_title('wide field imaging')
plt.show(block=False)
fig0.colorbar(im0)
del fig0, ax0, im0

# Define the number of harmonics to keep in each dimension
N = v07_2_image_wide_field_imaging.field.shape[0]
M = v07_2_image_wide_field_imaging.field.shape[1]
n_harmonics_x = N // 2
n_harmonics_y = M // 2

# Create a new zero-filled complex tensor with dimensions 2N x 2M
filtered_fft = torch.zeros(2 * N, 2 * M, dtype=torch.complex64).to(device)

# Copy the selected harmonics from the original FFT matrix to the new, larger FFT matrix
# Keep the first n_harmonics_x and n_harmonics_y harmonics in each quadrant
filtered_fft[:n_harmonics_x, :n_harmonics_y] = matrix_fft[:n_harmonics_x, :n_harmonics_y]
filtered_fft[-n_harmonics_x:, :n_harmonics_y] = matrix_fft[-n_harmonics_x:, :n_harmonics_y]
filtered_fft[:n_harmonics_x, -n_harmonics_y:] = matrix_fft[:n_harmonics_x, -n_harmonics_y:]
filtered_fft[-n_harmonics_x:, -n_harmonics_y:] = matrix_fft[-n_harmonics_x:, -n_harmonics_y:]

# Perform 2D Inverse Fourier Transform on the filtered, larger FFT matrix
extrapolated_matrix = torch.fft.ifft2(filtered_fft)

v07_2_image_wide_field_imaging.field = extrapolated_matrix

fig0, ax0 = plt.subplots()
im0 = ax0.imshow(np.abs(v07_2_image_wide_field_imaging.field.to('cpu').numpy()),
                 extent=v07_2_image_wide_field_imaging.extent.to('cpu').numpy())
ax0.set_title('wide field imaging ext')
plt.show(block=False)
fig0.colorbar(im0)
del fig0, ax0, im0

v20_object_fft = torch.fft.fftshift(torch.fft.fft2(abs(v04_padded_object.field)))
v21_regular_imaging_fft = torch.fft.fftshift(torch.fft.fft2(abs(v07_image_wide_field_imaging.field)))

fig00, axs00 = plt.subplots(2, 2)

ax = axs00[0, 0]
ax.set_title('object fft')
im2 = ax.imshow(np.abs(v20_object_fft.to('cpu').numpy()))
fig00.colorbar(im2)
del ax, im2

ax = axs00[0, 1]
ax.set_title('regular_imaging_fft')
im2 = ax.imshow(np.abs(v21_regular_imaging_fft.to('cpu').numpy()))
fig00.colorbar(im2)
del ax, im2

plt.show(block=False)

############################
###   confocal imaging   ###
############################
v08_temp_field = copy.deepcopy(v07_image_wide_field_imaging)
v08_temp_field.field = 0 * v08_temp_field.field
v08_temp_field.z = v00_system.u + v00_system.v

v16_final_confocal_field = copy.deepcopy(v04_padded_object)
v16_final_confocal_field.field = 0 * v16_final_confocal_field.field * 1j

points_around_for_ism = 100
ism_dim = (1 * points_around_for_ism + 1, 1 * points_around_for_ism + 1)

v17_ism_pic_by_resize1 = copy.deepcopy(v04_padded_object)
v17_ism_pic_by_resize2 = copy.deepcopy(v04_padded_object)
v17_ism_pic_no_resize = copy.deepcopy(v07_2_image_wide_field_imaging)
v17_ism_pic_by_resize1.field = 0 * v17_ism_pic_by_resize1.field * 1j
v17_ism_pic_by_resize2.field = 0 * v17_ism_pic_by_resize2.field * 1j
v17_ism_pic_no_resize.field = 0 * v17_ism_pic_no_resize.field * 1j
v18_ism_pic_by_down_sampling = copy.deepcopy(v04_padded_object)
v18_ism_pic_by_down_sampling.field = 0 * v18_ism_pic_by_down_sampling.field * 1j
v19_wide_field_by_sum = copy.deepcopy(v07_image_wide_field_imaging)
v19_wide_field_by_sum.field = 0 * v19_wide_field_by_sum.field

# row = column = 0
counter = 0
for row in tqdm(np.arange(v02_small_padded_field.field.shape[0] * 2)):
    for column in (np.arange(v02_small_padded_field.field.shape[1] * 2)):
        [x, y] = [column + 2 * v08_temp_field.padding_size, row + 2 * v08_temp_field.padding_size]
        counter = counter + 1

        # propagation v from image plane to lens
        field_in = copy.deepcopy(v08_temp_field)
        # propagate illumination from image to obj at specific point:
        field_in.field[y, x] = 1
        z_out = v00_system.u
        v09_field_before_lens = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=0)

        """
        v09_field_before_lens = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=1)
        """
        del field_in, z_out

        # Lens
        field_in = copy.deepcopy(v09_field_before_lens)
        v10_field_after_lens = prop.thin_lens(field_in, v00_system.wave_length, v00_system.lens_radius,
                                              v00_system.lens_center_pos, v00_system.f, plot=0)
        """
        v10_field_after_lens = prop.thin_lens(field_in, v00_system.wave_length, v00_system.lens_radius, v00_system.lens_center_pos, v00_system.f, plot=1)
        """
        del field_in

        # propagation u from lens obj plane
        field_in = copy.deepcopy(v10_field_after_lens)
        z_out = torch.tensor(0).to(device)
        v11_illumination_at_obj = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=0)

        """
        v11_illumination_at_obj = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=1)
        """
        del field_in, z_out

        # applying the confocal illumination
        v12_illuminated_obj = copy.deepcopy(v11_illumination_at_obj)
        v12_illuminated_obj.field = v04_padded_object.field * v11_illumination_at_obj.field
        """
        fig0, ax0 = plt.subplots()
        im1 = ax0.imshow(np.abs(v12_illuminated_obj.field.to('cpu').numpy()), extent=v12_illuminated_obj.extent.to('cpu').numpy())
        plt.show(block=False)
        del fig0, ax0, im0        
        """

        ## propagate the illuminated object to image plane
        # propagation u from object to lens
        field_in = copy.deepcopy(v12_illuminated_obj)
        z_out = v00_system.u
        v13_field_before_lens = prop.distance_z(field_in, z_out, v00_system.wave_length)
        """
        v13_field_before_lens = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=1)
        """
        del field_in, z_out

        # Lens
        field_in = copy.deepcopy(v13_field_before_lens)
        v14_field_after_lens = prop.thin_lens(field_in, v00_system.wave_length, v00_system.lens_radius,
                                              v00_system.lens_center_pos, v00_system.f)
        """
        v14_field_after_lens = prop.thin_lens(field_in, v00_system.wave_length, v00_system.lens_radius, v00_system.lens_center_pos, v00_system.f, plot=1)
        """
        del field_in

        # propagation v from lens to o
        field_in = copy.deepcopy(v14_field_after_lens)
        z_out = field_in.z + v00_system.v
        v15_field_at_image = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=0)
        """
        v15_field_at_image = prop.distance_z(field_in, z_out, v00_system.wave_length, plot=1)
        """
        del field_in, z_out

        v16_final_confocal_field.field[y, x] = v15_field_at_image.field[y, x]

        #########################
        #######    ISM    #######
        #########################
        area_for_ism = v15_field_at_image.field[y - points_around_for_ism:y + 1 + points_around_for_ism,
                       x - points_around_for_ism:x + 1 + points_around_for_ism]

        ##################
        ## resize image ##
        ##################
        # size = area_for_ism.shape
        # real = torch.randn((1, 1, size[0], size[1])).to(device)
        # img = torch.randn((1, 1, size[0], size[1])).to(device)
        # real[0, 0, :, :] = torch.real(area_for_ism)
        # img[0, 0, :, :] = torch.imag(area_for_ism)
        #
        # a = torchvision.transforms.Resize(ism_dim)
        # b = a(real)
        # c = torch.nn.functional.interpolate(real, ism_dim)
        # d = a(img)
        # e = torch.nn.functional.interpolate(img, ism_dim)
        #
        # resized_re_area1 = b[0, 0, :, :]
        # resized_re_area2 = c[0, 0, :, :]
        # resized_im_area1 = d[0, 0, :, :]
        # resized_im_area2 = e[0, 0, :, :]
        # resized_area1 = resized_re_area1 + 1j * resized_im_area1
        # resized_area2 = resized_re_area2 + 1j * resized_im_area2
        # mat = real + img
        # del resized_re_area1, resized_re_area2, resized_im_area1, resized_im_area2
        # del a, b, c, d, e, real, img, size
        start_row = int(y - 0.5 * points_around_for_ism)
        end_row = int(y + 1 + 0.5 * points_around_for_ism)
        start_col = int(x - 0.5 * points_around_for_ism)
        end_col = int(x + 1 + 0.5 * points_around_for_ism)
        # a = v17_ism_pic_by_resize1.field[start_row:end_row, start_col:end_col]
        # v17_ism_pic_by_resize1.field[start_row:end_row, start_col:end_col] += resized_area1
        # v17_ism_pic_by_resize2.field[start_row:end_row, start_col:end_col] += resized_area2

        rows_idx_to_cut = torch.arange(0, area_for_ism.shape[0], 2).to(device)
        columns_idx_to_cut = torch.arange(0, area_for_ism.shape[1], 2).to(device)
        down_sampled_area = area_for_ism[rows_idx_to_cut, :][:, columns_idx_to_cut]
        v18_ism_pic_by_down_sampling.field[start_row:end_row, start_col:end_col] += down_sampled_area
        del area_for_ism, rows_idx_to_cut, columns_idx_to_cut


        start_row2 = int(2 * y - points_around_for_ism)
        end_row2 = int(2 * y + 1 + points_around_for_ism)
        start_col2 = int(2 * x - points_around_for_ism)
        end_col2 = int(2 * x + 1 + points_around_for_ism)
        # v17_ism_pic_no_resize.field[start_row2:end_row2, start_col2:end_col2] += mat[0, 0, :, :]
        v19_wide_field_by_sum.field += v15_field_at_image.field

        del start_row, end_row, start_col, end_col, down_sampled_area, resized_area1, resized_area2, v15_field_at_image, a, x, y
del counter, column, row, points_around_for_ism, ism_dim

end = time.time()
time_el = (end - start) / 60
print(time_el)

fig0, ax0 = plt.subplots()
im0 = ax0.imshow(np.abs(v07_2_image_wide_field_imaging.field.to('cpu').numpy()),
                 extent=v07_2_image_wide_field_imaging.extent.to('cpu').numpy())
ax0.set_title('wide field imaging ext')
plt.show(block=False)
fig0.colorbar(im0)
del fig0, ax0, im0

fig0, ax0 = plt.subplots()
im0 = ax0.imshow(np.abs(v17_ism_pic_no_resize.field.to('cpu').numpy()),
                 extent=v17_ism_pic_no_resize.extent.to('cpu').numpy())
ax0.set_title('ism ext')
plt.show(block=False)
fig0.colorbar(im0)
del fig0, ax0, im0

fig0, ax0 = plt.subplots()
im0 = ax0.imshow(np.abs(v18_ism_pic_by_down_sampling.field.to('cpu').numpy()),
                 extent=v18_ism_pic_by_down_sampling.extent.to('cpu').numpy())
ax0.set_title('ism')
plt.show(block=False)
fig0.colorbar(im0)
del fig0, ax0, im0

v22_confocal_fft = torch.fft.fftshift(torch.fft.fft2(abs(v16_final_confocal_field.field)))
v23_ism_fft1 = torch.fft.fftshift(torch.fft.fft2(abs(v17_ism_pic_by_resize1.field)))
v23_ism_fft2 = torch.fft.fftshift(torch.fft.fft2(abs(v17_ism_pic_by_resize2.field)))

ax = axs00[1, 0]
ax.set_title('confocal fft')
im2 = ax.imshow(np.abs(v22_confocal_fft.to('cpu').numpy()))
fig00.colorbar(im2)
del ax, im2

ax = axs00[1, 1]
ax.set_title('v29_ism_fft2')
im2 = ax.imshow(np.abs(v23_ism_fft2.to('cpu').numpy()))
fig00.colorbar(im2)
del ax, im2
plt.show(block=False)
# # field_z = padded_field_z[padded_size: dim_x - padded_size, padded_size:dim_x - padded_size]
# fig, ax = plt.subplots()
# ax.set_title('field' )
# im1 = ax.imshow(circ_iris, extent=padded_extent)
# plt.show(block=False)

del fig00, axs00, start, end, time_el, device

bk = {}
bk.update({'v00_system': v00_system})
bk.update({'v01_initial_field': v01_initial_field})
bk.update({'v02_small_padded_field': v02_small_padded_field})
bk.update({'v03_filtered_small_padded_field': v03_filtered_small_padded_field})
bk.update({'v04_padded_object': v04_padded_object})
bk.update({'v05_field_before_lens': v05_field_before_lens})
bk.update({'v06_field_after_lens': v06_field_after_lens})
bk.update({'v07_image_wide_field_imaging': v07_image_wide_field_imaging})
bk.update({'v16_final_confocal_field': v16_final_confocal_field})
bk.update({'v17_ism_pic_by_resize1': v17_ism_pic_by_resize1})
bk.update({'v17_ism_pic_by_resize2': v17_ism_pic_by_resize2})
bk.update({'v18_ism_pic_by_down_sampling': v18_ism_pic_by_down_sampling})
bk.update({'v19_wide_field_by_sum': v19_wide_field_by_sum})

# save session
with open('./ism example single lens r 55 cm.pkl', 'wb') as f:
    # Move tensors to CPU device before saving
    bk_cpu = {}
    for name, creature in bk.items():
        members = [attr for attr in dir(creature) if
                   not callable(getattr(creature, attr)) and not attr.startswith("__")]
        for member in members:
            attr_value = getattr(creature, member)

            if isinstance(attr_value, torch.Tensor):
                setattr(creature, member, attr_value.to(torch.device('cpu')))

            if member == 'mesh':
                for i in range(len(attr_value)):
                    if isinstance(attr_value[i], torch.Tensor):
                        setattr(creature, member, attr_value[i].to(torch.device('cpu')))

        bk_cpu[name] = creature
    pickle.dump(bk_cpu, f)

plt.close('all')
